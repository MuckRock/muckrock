"""
Email handler for request emails
"""

# pylint: disable-msg=E0611

from django.core.files import File
from django.template.loader import render_to_string

import logging
from config.settings import relay
from lamson.routing import route, stateless

import os
from datetime import datetime
from email.utils import parseaddr
from tempfile import NamedTemporaryFile

from foia.models import FOIARequest, FOIADocument, FOIACommunication, FOIAFile
from foia.tasks import upload_document_cloud

DOC_CLOUD_TYPES = ['application/pdf']
IGNORE_TYPES = []
TEXT_TYPES = ['text/plain']

# pylint: disable-msg=C0103

@route('(address)@(host)')
@stateless
def REQUEST(message, address=None, host=None):
    """Request auto handler"""
    # pylint: disable-msg=E1101

    if not _allowed_email(parseaddr(message['from'])[1]):
        logging.warning('Bad sender: %s', message['from'])
        message['subject'] = 'Bad Sender: %s' % message['subject']
        relay.deliver(message, To='requests@muckrock.com')
        return

    try:
        foia = FOIARequest.objects.get(mail_id=address)
        communication = ''
        attachments = []
        for part in message.to_message().walk():
            if part.get_content_maintype() == 'multipart':
                # just a container for other parts
                continue
            content_type = part.get_content_type()
            file_name = part.get_filename()
            if content_type in TEXT_TYPES:
                communication += part.get_payload()
                attachments.append('Add to body text - type: %s name: %s' %
                                   (content_type, file_name))

            if content_type not in IGNORE_TYPES:
                if file_name and content_type in DOC_CLOUD_TYPES:
                    _upload_doc_cloud(foia, file_name, part, message['from'])
                    attachments.append('Add as a doc cloud - type: %s name: %s' %
                                       (content_type, file_name))
                elif file_name:
                    _upload_file(foia, file_name, part)
                    attachments.append('Add as a file - type: %s name: %s' %
                                       (content_type, file_name))
                else:
                    attachments.append('Skipped due to no name - type: %s name: %s' %
                                       (content_type, file_name))

        FOIACommunication.objects.create(
                foia=foia, from_who=message['from'], date=datetime.now(), response=True,
                full_html=False, communication=communication)

        relay.deliver(message, To='requests@muckrock.com')
        relay.send(From='%s@%s' % (address, host), To='requests@muckrock.com',
                   Subject='[RESPONSE] Freedom of Information Request: %s' % foia.title,
                   Body=render_to_string('foia/admin_request.txt',
                                         {'request': foia, 'attachments': attachments,
                                          'message': message}))

        foia.updated()

        # Use NLTK to try and automatically set updated status

    except FOIARequest.DoesNotExist:
        logging.warning('Invalid address: %s', address)
        message['subject'] = 'Invalid address: %s' % address
        relay.deliver(message, To='requests@muckrock.com')


# factor commonalities out of these two?

def _upload_file(foia, file_name, part):
    """Upload a file to attach to a FOIA request"""
    # pylint: disable-msg=E1101

    with NamedTemporaryFile() as temp_file:
        temp_file.write(part.get_payload(decode=True))
        foia_file = FOIAFile(foia=foia)
        foia_file.ffile.save(file_name, File(temp_file))
        foia_file.save()

def _upload_doc_cloud(foia, file_name, part, sender):
    """Upload a document cloud to attach to a FOIA request"""
    # pylint: disable-msg=E1101

    access = 'private' if foia.is_embargo() else 'public'
    source = foia.agency.name if foia.agency else sender

    with NamedTemporaryFile() as temp_file:
        temp_file.write(part.get_payload(decode=True))
        foia_doc = FOIADocument(foia=foia, title=os.path.splitext(file_name)[0],
                                source=source, access=access, date=datetime.now())
        foia_doc.document.save(file_name, File(temp_file))
        foia_doc.save()
        upload_document_cloud.apply_async(args=[foia_doc.pk, False], countdown=3)

def _allowed_email(email):
    """Is this an allowed email?"""

    allowed_email_tlds = ['.gov', '.mil', '.state.ma.us', '.state.ny.us']
    if any(email.endswith(tld) for tld in allowed_email_tlds):
        return True
    # check agency database here
    return False
