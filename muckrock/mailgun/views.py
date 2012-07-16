"""
Views for mailgun
"""

from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.core.mail import EmailMessage, send_mail
from django.core.validators import email_re
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

import hashlib
import hmac
import logging
import os
import sys
import time
from datetime import datetime
from email.utils import parseaddr

from foia.models import FOIARequest, FOIACommunication, FOIADocument, FOIAFile
from foia.tasks import upload_document_cloud
from fields import email_separator_re
from settings import MAILGUN_ACCESS_KEY

logger = logging.getLogger(__name__)

@csrf_exempt
def handle_request(request, mail_id):
    """Handle incoming mailgun FOI request messages"""

    post = request.POST
    if not _verify(post):
        return HttpResponseForbidden()
    from_ = post.get('from')

    try:
        foia = FOIARequest.objects.get(mail_id=mail_id)
        from_realname, from_email = parseaddr(from_)

        if not _allowed_email(from_email, foia):
            logger.warning('Bad Sender: %s', from_)
            _forward(post, request.FILES, 'Bad Sender')
            return HttpResponse('WARNING')

        comm = FOIACommunication.objects.create(
                foia=foia, from_who=from_realname[:255],
                to_who=foia.user.get_full_name(), response=True,
                date=datetime.now(), full_html=False,
                communication=post.get('stripped-text'))

        # handle attachments
        for file_ in request.FILES.itervalues():
            type_ = _file_type(file_)
            if type_ == 'doc_cloud':
                _upload_doc_cloud(foia, file_, from_)
            elif type_ == 'file':
                _upload_file(foia, file_, from_)

        _forward(post, request.FILES)
        send_mail('[RESPONSE] Freedom of Information Request: %s' % foia.title,
                  render_to_string('foia/admin_request.txt',
                                   {'request': foia, 'post': post}),
                  'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

        foia.email = from_email

        other_emails = [email_separator_re.sub('', email.strip()) for email
                        in post.get('To', '').split(',') + 
                           post.get('Cc', '').split(',')
                        if email]
        foia.other_emails = ','.join(email for email in other_emails
                                     if email_re.match(email) and
                                        not email.endswith('muckrock.com'))
        foia.save()
        foia.update(comm.anchor())

        # NLTK

    except FOIARequest.DoesNotExist:
        logger.warning('Invalid Address: %s', mail_id)
        _forward(post, request.FILES, 'Invalid Address')
        return HttpResponse('WARNING')
    except Exception:
        # If anything I haven't accounted for happens, at the very least forward
        # the email to requests so it isn't lost
        logger.error('Uncaught Mailgun Exception: %s', mail_id, exc_info=sys.exc_info())
        _forward(post, request.FILES, 'Uncaught Mailgun Exception')
        return HttpResponse('ERROR')

    return HttpResponse('OK')

@csrf_exempt
def fax(request):
    """Handle fax confirmations"""

    if not _verify(request.POST):
        return HttpResponseForbidden()

    _forward(request.POST, request.FILES)
    return HttpResponse('OK')

def _verify(post):
    """Verify that the message is from mailgun"""
    token = post.get('token')
    timestamp = post.get('timestamp')
    signature = post.get('signature')
    return (signature == hmac.new(key=MAILGUN_ACCESS_KEY,
                                  msg='%s%s' % (timestamp, token),
                                  digestmod=hashlib.sha256).hexdigest()) \
           and int(timestamp) + 300 > time.time()

def _forward(post, files, title=''):
    """Forward an email from mailgun to admin"""
    if title:
        subject = '%s: %s' % (title, post.get('subject'))
    else:
        subject = post.get('subject')
    subject = subject.replace('\r', '').replace('\n', '')

    email = EmailMessage(subject, post.get('body-plain'),
                         post.get('From'), ['requests@muckrock.com'])
    for file_ in files.itervalues():
        email.attach(file_.name, file_.read(), file_.content_type)

    email.send(fail_silently=False)

def _upload_file(foia, file_, sender):
    """Upload a file to attach to a FOIA request"""
    # pylint: disable=E1101

    foia_file = FOIAFile(foia=foia, date=datetime.now(), source=sender[:70])
    foia_file.ffile.save(file_.name, file_)
    foia_file.save()

def _upload_doc_cloud(foia, file_, sender):
    """Upload a document cloud to attach to a FOIA request"""
    # pylint: disable=E1101

    access = 'private' if foia.is_embargo() else 'public'
    source = foia.agency.name if foia.agency else sender

    foia_doc = FOIADocument(foia=foia, title=os.path.splitext(file_.name)[0],
                            source=source, access=access, date=datetime.now())
    foia_doc.document.save(file_.name, file_)
    foia_doc.save()
    upload_document_cloud.apply_async(args=[foia_doc.pk, False], countdown=3)

def _allowed_email(email, foia):
    """Is this an allowed email?"""

    email = email.lower()
    state_tlds = ['state.%s.us' % a.lower() for (a, _) in STATE_CHOICES
                                            if a not in ('AS', 'DC', 'GU', 'MP', 'PR', 'VI')]
    allowed_tlds = [
        '.gov',
        '.mil',
        '.muckrock.com',
        '@muckrock.com',
        ] + state_tlds
    if foia.email and '@' in foia.email and email.endswith(foia.email.split('@')[1].lower()):
        return True
    if foia.agency and email in [i.lower() for i in foia.agency.get_other_emails()]:
        return True
    return any(email.endswith(tld) for tld in allowed_tlds)

def _file_type(file_):
    """Determine the attachment's file type"""

    doc_cloud_types = [
        ('application/pdf', 'pdf'),
        ('application/msword', 'doc'),
        ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
        ]
    ignore_types = [('application/x-pkcs7-signature', 'p7s')]

    if any(file_.content_type == itt or file_.name.endswith(ite) for itt, ite in ignore_types):
        return 'ignore'
    elif any(file_.content_type == dtt or file_.name.endswith(dte) for dtt, dte in doc_cloud_types):
        return 'doc_cloud'
    else:
        return 'file'

