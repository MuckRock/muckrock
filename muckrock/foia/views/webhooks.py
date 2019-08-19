"""
Webhooks for FOIA app
"""

# Django
from django.conf import settings
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.views.decorators.csrf import csrf_exempt

# Standard Library
import hashlib
import hmac
import json
import logging
import time

# Third Party
import dateutil.parser

# MuckRock
from muckrock.communication.models import MailCommunication


@csrf_exempt
def lob_webhook(request):
    """Handle Lob Webhook"""

    if not _validate_lob(
        request.META['HTTP_LOB_SIGNATURE'],
        request.META['HTTP_LOB_SIGNATURE_TIMESTAMP'],
        request.body,
    ):
        return HttpResponseForbidden()

    try:
        data = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("JSON decode error")

    try:
        mail_id = data['body']['metadata']['mail_id']
    except KeyError:
        return HttpResponseBadRequest("Missing JSON data")

    mail = MailCommunication.objects.filter(pk=mail_id).first()

    if mail is not None:
        mail.events.create(
            datetime=dateutil.parser.parse(data['date_created']),
            event=data['event_type']['id'],
        )

    return HttpResponse("OK")


def _validate_lob(signature, timestamp, body):
    """Verify the message is from Lob"""
    print timestamp
    print body
    print settings.LOB_WEBHOOK_KEY
    digest = hmac.new(
        key=settings.LOB_WEBHOOK_KEY.encode('utf-8'),
        msg=u'{}.{}'.format(timestamp, body).encode('utf-8'),
        digestmod=hashlib.sha256,
    ).hexdigest()
    match = hmac.compare_digest(signature, digest)
    return match and int(timestamp) + 300 > time.time()
