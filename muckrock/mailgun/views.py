"""
Views for mailgun
"""

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

import hashlib
import hmac
import json
import logging
import re
import sys
import time
from datetime import datetime
from email.utils import getaddresses
from functools import wraps

from muckrock.agency.models import AgencyEmail
from muckrock.communication.models import (
        EmailAddress,
        EmailCommunication,
        EmailError,
        EmailOpen,
        PhoneNumber,
        FaxCommunication,
        FaxError,
        )
from muckrock.foia.models import (
        FOIARequest,
        FOIACommunication,
        RawEmail,
        )
from muckrock.foia.tasks import classify_status
from muckrock.task.models import (
        OrphanTask,
        ResponseTask,
        ReviewAgencyTask,
        )

logger = logging.getLogger(__name__)


def _make_orphan_comm(from_email, to_emails, cc_emails,
        subject, post, files, foia):
    """Make an orphan communication"""
    # pylint: disable=too-many-arguments
    if from_email:
        agencies = from_email.agencies.all()
    else:
        agencies = []
    if len(agencies) == 1:
        from_user = agencies[0].get_user()
    else:
        from_user = None
    comm = FOIACommunication.objects.create(
            from_user=from_user,
            response=True,
            subject=subject[:255],
            date=datetime.now(),
            communication=_get_mail_body(post),
            likely_foia=foia,
            )
    email_comm = EmailCommunication.objects.create(
            communication=comm,
            sent_datetime=datetime.now(),
            from_email=from_email,
            )
    email_comm.to_emails.set(to_emails)
    email_comm.cc_emails.set(cc_emails)
    RawEmail.objects.create(
        email=email_comm,
        raw_email='%s\n%s' % (
            post.get('message-headers', ''),
            post.get('body-plain', '')),
        )
    comm.process_attachments(files)

    return comm


def _get_mail_body(post):
    """Try to get the stripped-text unless it looks like that parsing failed,
    then get the full plain body"""
    stripped_text = post.get('stripped-text', '')
    bad_text = [
            # if stripped-text is blank or not present
            '',
            '\n',
            # the following are form Seattle's automated system
            # they seem to confuse mailgun's parser
            '--- Please respond above this line ---',
            '--- Please respond above this line ---\n',
            ]
    if stripped_text in bad_text:
        return post.get('body-plain')
    else:
        return '%s\n%s' % (
                post.get('stripped-text', ''),
                post.get('stripped-signature', ''))


def mailgun_verify(function):
    """Decorator to verify mailgun webhooks"""
    @wraps(function)
    def wrapper(request):
        """Wrapper"""
        if _verify(request.POST):
            return function(request)
        else:
            return HttpResponseForbidden()
    return wrapper


def get_common_webhook_params(function):
    """Decorator to handle getting the communication for mailgun webhooks"""
    @wraps(function)
    def wrapper(request):
        """Wrapper"""
        email_id = request.POST.get('email_id')
        timestamp = request.POST['timestamp']
        timestamp = datetime.fromtimestamp(int(timestamp))

        if email_id:
            email_comm = EmailCommunication.objects.filter(pk=email_id).first()
        else:
            email_comm = None

        if email_comm:
            function(request, email_comm, timestamp)
        else:
            logger.warning(
                    'No email comm for %s webhook: %s',
                    function.__name__,
                    request.POST,
                    )

        return HttpResponse('OK')
    return wrapper


@mailgun_verify
@csrf_exempt
def route_mailgun(request):
    """Handle routing of incoming mail with proper header parsing"""

    post = request.POST
    # The way spam hero is currently set up, all emails are sent to the same
    # address, so we must parse to headers to find the recipient.  This can
    # cause duplicate messages if one email is sent to or CC'd to multiple
    # addresses @requests.muckrock.com.  To try and avoid this, we will cache
    # the message id, which should be a unique identifier for the message.
    # If it exists int he cache, we will stop processing this email.  The
    # ID will be cached for 5 minutes - duplicates should normally be processed
    # within seconds of each other.
    message_id = (
            post.get('Message-ID') or
            post.get('Message-Id') or
            post.get('message-id'))
    if message_id:
        # cache.add will return False if the key is already present
        if not cache.add(message_id, 1, 300):
            return HttpResponse('OK')

    p_request_email = re.compile(r'(\d+-\d{3,10})@%s' % settings.MAILGUN_SERVER_NAME)
    tos = post.get('To', '') or post.get('to', '')
    ccs = post.get('Cc', '') or post.get('cc', '')
    name_emails = getaddresses([tos.lower(), ccs.lower()])
    logger.info('Incoming email: %s - %s', name_emails, post.get('Subject', ''))
    for _, email in name_emails:
        m_request_email = p_request_email.match(email)
        if m_request_email:
            _handle_request(request, m_request_email.group(1))
        elif email.endswith('@%s' % settings.MAILGUN_SERVER_NAME):
            _catch_all(request, email)
    return HttpResponse('OK')

def _parse_email_headers(post):
    """Parse email headers and return email address models"""
    from_ = post.get('From', '')
    to_ = post.get('To') or post.get('to', '')
    cc_ = post.get('Cc') or post.get('cc', '')
    from_email = EmailAddress.objects.fetch(from_)
    to_emails = EmailAddress.objects.fetch_many(to_)
    cc_emails = EmailAddress.objects.fetch_many(cc_)
    return from_email, to_emails, cc_emails


def _handle_request(request, mail_id):
    """Handle incoming mailgun FOI request messages"""
    # this function needs to be refactored
    # pylint: disable=broad-except
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    post = request.POST
    from_email, to_emails, cc_emails = _parse_email_headers(post)
    subject = post.get('Subject') or post.get('subject', '')

    try:
        foia = FOIARequest.objects.get(mail_id=mail_id)

        # extra logging for next request portals for now
        if foia.portal and foia.portal.type == 'nextrequest':
            _log_mail(request)

        if from_email is not None:
            email_allowed = from_email.allowed(foia)
        else:
            email_allowed = False
        if not email_allowed:
            msg, reason = ('Bad Sender', 'bs')
        if foia.block_incoming:
            msg, reason = ('Incoming Blocked', 'ib')
        if not email_allowed or foia.block_incoming:
            logger.warning('%s: %s', msg, from_email)
            comm = _make_orphan_comm(
                    from_email,
                    to_emails,
                    cc_emails,
                    subject,
                    post,
                    request.FILES,
                    foia,
                    )
            OrphanTask.objects.create(
                reason=reason,
                communication=comm,
                address=mail_id)
            return HttpResponse('WARNING')

        # if this isn't a known email for this agency, add it
        if not from_email.agencies.filter(pk=foia.agency.pk).exists():
            AgencyEmail.objects.create(
                    agency=foia.agency,
                    email=from_email,
                    )

        # if this request is using a portal, hide the incoming messages
        hidden = foia.portal is not None

        comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=foia.agency.get_user(),
                to_user=foia.user,
                subject=subject[:255],
                response=True,
                date=datetime.now(),
                communication=_get_mail_body(post),
                hidden=hidden,
                )
        email_comm = EmailCommunication.objects.create(
                communication=comm,
                sent_datetime=datetime.now(),
                from_email=from_email,
                )
        email_comm.to_emails.set(to_emails)
        email_comm.cc_emails.set(cc_emails)
        RawEmail.objects.create(
            email=email_comm,
            raw_email='%s\n%s' % (post.get('message-headers', ''), post.get('body-plain', '')))
        comm.process_attachments(request.FILES)

        # resolve any stale agency tasks for this agency
        if foia.agency:
            foia.agency.unmark_stale()
        comm.extract_tracking_id()

        if foia.portal:
            foia.portal.receive_msg(comm)
        else:
            task = ResponseTask.objects.create(communication=comm)
            classify_status.apply_async(args=(task.pk,), countdown=30 * 60)
            comm.create_agency_notifications()

        new_cc_emails = [e for e in (to_emails + cc_emails)
                if e.domain not in
                (settings.MAILGUN_SERVER_NAME, 'muckrock.com')]
        foia.email = from_email
        foia.cc_emails.set(new_cc_emails)

        if foia.status == 'ack':
            foia.status = 'processed'
        foia.save(comment='incoming mail')

    except FOIARequest.DoesNotExist:
        logger.warning('Invalid Address: %s', mail_id)
        try:
            # try to get the foia by the PK before the dash
            foia = FOIARequest.objects.get(pk=mail_id.split('-')[0])
        except FOIARequest.DoesNotExist:
            foia = None
        comm = _make_orphan_comm(
                from_email,
                to_emails,
                cc_emails,
                subject,
                post,
                request.FILES,
                foia,
                )
        OrphanTask.objects.create(
            reason='ia',
            communication=comm,
            address=mail_id)
        return HttpResponse('WARNING')
    except Exception as exc:
        # If anything I haven't accounted for happens, at the very least forward
        # the email to requests so it isn't lost
        logger.error(
                'Uncaught Mailgun Exception - %s: %s',
                mail_id,
                exc,
                exc_info=sys.exc_info(),
                )
        _forward(post, request.FILES, 'Uncaught Mailgun Exception', info=True)
        return HttpResponse('ERROR')

    return HttpResponse('OK')


def _catch_all(request, address):
    """Handle emails sent to other addresses"""

    post = request.POST
    from_email, to_emails, cc_emails = _parse_email_headers(post)
    subject = post.get('Subject') or post.get('subject', '')

    if from_email.allowed():
        comm = _make_orphan_comm(
                from_email,
                to_emails,
                cc_emails,
                subject,
                post,
                request.FILES,
                None,
                )
        OrphanTask.objects.create(
            reason='ia',
            communication=comm,
            address=address)

    return HttpResponse('OK')


@mailgun_verify
@csrf_exempt
@get_common_webhook_params
def bounces(request, email_comm, timestamp):
    """Notify when an email is bounced or dropped"""

    recipient = EmailAddress.objects.fetch(request.POST.get('recipient', ''))
    event = request.POST.get('event', '')
    if event == 'bounced':
        error = request.POST.get('error', '')
    elif event == 'dropped':
        error = request.POST.get('description', '')
    else:
        error = ''

    EmailError.objects.create(
            email=email_comm,
            datetime=timestamp,
            recipient=recipient,
            code=request.POST.get('code', ''),
            error=error,
            event=event,
            reason=request.POST.get('reason', ''),
            )
    recipient.status = 'error'
    recipient.save()
    ReviewAgencyTask.objects.ensure_one_created(
            agency=email_comm.communication.foia.agency,
            resolved=False,
            )

    # ensure we don't create an infinite loop of emails
    # we expect the reported recipient to be the same as the foia
    # email, and we expect that email to have been just marked
    # as in an error state
    foia = email_comm.communication.foia
    recipient_is_foia_email = foia.email == recipient
    foia_email_is_error = foia.email.status == 'error'
    recipient_is_cc = email_comm.cc_emails.filter(email=recipient)
    if not recipient_is_foia_email:
        logger.error(
                'Bounce: recipient does not match foia email: %s - %s',
                recipient,
                foia.email,
                )
    elif not foia_email_is_error:
        logger.error(
                'Bounce: foia email is not marked as error: %s',
                foia.email,
                )
    elif not recipient_is_cc:
        # if the foia email matches and is not a CC, we resubmit
        # in order to fall back to fax or snail mail
        email_comm.communication.foia.submit(switch=True)


@mailgun_verify
@csrf_exempt
@get_common_webhook_params
def opened(request, email_comm, timestamp):
    """Notify when an email has been opened"""
    recipient = EmailAddress.objects.fetch(request.POST.get('recipient', ''))
    EmailOpen.objects.create(
            email=email_comm,
            datetime=timestamp,
            recipient=recipient,
            city=request.POST.get('city', ''),
            region=request.POST.get('region', ''),
            country=request.POST.get('country', ''),
            client_type=request.POST.get('client-type', ''),
            client_name=request.POST.get('client-name', ''),
            client_os=request.POST.get('client-os', ''),
            device_type=request.POST.get('device-type', ''),
            user_agent=request.POST.get('user-agent', '')[:255],
            ip_address=request.POST.get('ip', ''),
            )


@mailgun_verify
@csrf_exempt
@get_common_webhook_params
def delivered(_request, email_comm, timestamp):
    """Notify when an email has been delivered"""
    email_comm.confirmed_datetime = timestamp
    email_comm.save()


@csrf_exempt
def phaxio_callback(request):
    """Handle Phaxio callbacks"""
    # pylint: disable=too-many-branches
    url = 'https://%s%s' % (
            settings.MUCKROCK_URL,
            reverse('phaxio-callback'),
            )
    if not _validate_phaxio(
            settings.PHAXIO_CALLBACK_TOKEN,
            url,
            request.POST,
            request.FILES,
            request.META['HTTP_X_PHAXIO_SIGNATURE'],
            ):
        return HttpResponseForbidden()

    fax_info = json.loads(request.POST['fax'])
    fax_id = fax_info['tags'].get('fax_id')
    error_count = fax_info['tags'].get('error_count')
    if fax_id:
        fax_comm = FaxCommunication.objects.filter(pk=fax_id).first()
    else:
        fax_comm = None

    if not fax_comm:
        logger.warning(
                'No fax comm for phaxio callback: %s',
                request.POST,
                )
    else:
        if 'completed_at' in fax_info:
            date = datetime.fromtimestamp(int(fax_info['completed_at']))
        else:
            date = datetime.now()
        if request.POST['success'] == 'true':
            fax_comm.confirmed_datetime = date
            fax_comm.save()
        else:
            for recipient in fax_info['recipients']:
                number, _ = PhoneNumber.objects.get_or_create(
                        number=recipient['number'],
                        defaults={'type': 'fax'},
                        )
                FaxError.objects.create(
                        fax=fax_comm,
                        datetime=date,
                        recipient=number,
                        error_type=recipient['error_type'],
                        error_code=recipient['error_code'],
                        error_id=int(recipient['error_id']),
                        )
                # the following phaxio error IDs all correspond to
                # Phone Number Not Operational - all other errors are considered
                # temporary for now
                perm_error_ids = set([34, 47, 49, 91, 107, 109, 116, 123])
                temp_failure = int(recipient['error_id']) not in perm_error_ids
                if temp_failure and error_count < 4:
                    # retry with exponential back off
                    fax_comm.communication.foia_submit(
                            fax_error_count=error_count + 1)
                else:
                    number.status = 'error'
                    number.save()
                    ReviewAgencyTask.objects.ensure_one_created(
                            agency=fax_comm.communication.foia.agency,
                            resolved=False,
                            )
                    fax_comm.communication.foia.submit(switch=True)

    return HttpResponse('OK')


def _validate_phaxio(token, url, parameters, files, signature):
    """Validate Phaxio callback"""
    # sort the post fields and add them to the URL
    for key in sorted(parameters.keys()):
        url += '{}{}'.format(key, parameters[key])

    # sort the files and add their SHA1 sums to the URL
    for filename in sorted(files.keys()):
        file_hash = hashlib.sha1()
        file_hash.update(files[filename].read())
        files[filename].stream.seek(0)
        url += '{}{}'.format(filename, file_hash.hexdigest())

    digest = hmac.new(
            key=token.encode('utf-8'),
            msg=url.encode('utf-8'),
            digestmod=hashlib.sha1,
            ).hexdigest()
    return signature == digest


def _verify(post):
    """Verify that the message is from mailgun"""
    token = post.get('token', '')
    timestamp = post.get('timestamp', '')
    signature = post.get('signature', '')
    signature_ = hmac.new(
            key=settings.MAILGUN_ACCESS_KEY,
            msg='%s%s' % (timestamp, token),
            digestmod=hashlib.sha256,
            ).hexdigest()
    return signature == signature_ and int(timestamp) + 300 > time.time()


def _forward(post, files, title='', extra_content='', info=False):
    """Forward an email from mailgun to admin"""
    if title:
        subject = '%s: %s' % (title, post.get('subject', ''))
    else:
        subject = post.get('subject', '')
    subject = subject.replace('\r', '').replace('\n', '')

    if extra_content:
        body = '%s\n\n%s' % (extra_content, post.get('body-plain'))
    else:
        body = post.get('body-plain')
    if not body:
        body = 'This email intentionally left blank'

    to_addresses = ['requests@muckrock.com']
    if info:
        to_addresses.append('info@muckrock.com')
    email = EmailMessage(subject, body, post.get('From'), to_addresses)
    for file_ in files.itervalues():
        email.attach(file_.name, file_.read(), file_.content_type)

    email.send(fail_silently=False)

def _log_mail(request):
    """Log a request"""
    body = []
    for key, value in request.POST.iteritems():
        body.append('\n{}:'.format(key))
        body.append(unicode(value))
    email = EmailMessage(
            '[NEXTREQUEST LOG]',
            '\n'.join(body),
            'info@muckrock.com',
            ['mitch@muckrock.com'],
            )
    email.send(fail_silently=False)
