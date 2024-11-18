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
import lob

# MuckRock
from muckrock.communication.models import MailCommunication
from muckrock.core.utils import new_action

logger = logging.getLogger(__name__)


@csrf_exempt
def lob_webhook(request):
    """Handle Lob Webhook"""

    logger.info("Lob webhook")

    if not _validate_lob(
        request.META["HTTP_LOB_SIGNATURE"],
        request.META["HTTP_LOB_SIGNATURE_TIMESTAMP"],
        request.body,
    ):
        logger.warning("Lob webhook failed verification: %s", request.META)
        return HttpResponseForbidden()

    try:
        data = json.loads(request.body)
    except ValueError:
        logger.error("Lob webhook JSON decode error")
        return HttpResponseBadRequest("JSON decode error")

    try:
        mail_id = data["body"]["metadata"]["mail_id"]
    except KeyError:
        # check failed does not have mail_id set
        if data["event_type"]["id"] == "check.failed":
            check_id = data["reference_id"]
            logger.info("Lob webhook: Check Failed %s", check_id)
            check = lob.Check.retrieve(check_id)
            mail_id = check["metadata"]["mail_id"]
            mail = MailCommunication.objects.get(pk=mail_id)
            mail.communication.foia.flaggedtask_set.create(
                category="payment",
                text="Lob check failed.  Please investigate.\n"
                f"https://dashboard.lob.com/checks/{check_id}",
            )
            return HttpResponse("OK")
        else:
            logger.error("Lob webhook JSON missing data")
            return HttpResponseBadRequest("Missing JSON data")

    mail = MailCommunication.objects.filter(pk=mail_id).first()

    if mail is None:
        logger.error("Missing mail communication for mail_id: %s", mail_id)
    elif mail is not None:
        event = mail.events.create(
            datetime=dateutil.parser.parse(data["date_created"]),
            event=data["event_type"]["id"],
        )
        if (
            event.event == "check.processed_for_delivery"
            and settings.CHECK_NOTIFICATIONS
        ):
            foia = mail.communication.foia
            action = new_action(
                foia.agency, "check processed for delivery", target=foia, public=False
            )
            foia.notify(action)

    return HttpResponse("OK")


def _validate_lob(signature, timestamp, body):
    """Verify the message is from Lob"""
    digest = hmac.new(
        key=settings.LOB_WEBHOOK_KEY.encode("utf8"),
        # timestamp is a string, body is already bytes
        msg=timestamp.encode("utf8") + b"." + body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    match = hmac.compare_digest(signature, digest)
    logger.info(
        "Lob webhook validate debug: "
        "signature: %s timestamp: %s digest: %s match: %s time: %s",
        signature,
        timestamp,
        digest,
        match,
        time.time(),
    )
    return match and int(timestamp) + 300 > time.time()
