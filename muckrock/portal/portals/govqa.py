"""
Automate some parts of GovQA portal handling
"""

# Django
from django.conf import settings

# Standard Library
import logging
import sys

# Third Party
import dateutil
import requests
from furl import furl
from govqa.base import GovQA
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.core.utils import parse_header
from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.models.file import get_path
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task
from muckrock.task.models import FlaggedTask

logger = logging.getLogger(__name__)


class GovQAPortal(ManualPortal):
    """GovQA portal integreation"""

    def _send_msg(self, comm, **kwargs):
        """Send a message via email if possible"""
        # Note:
        # Disabling this for now, as it does not seem to work
        # Rename method back to send_msg to re-enable if we figure out
        # how to get email replies in GovQA to work

        # send an email for not new submissions, which have a valid email address,
        # only for staff users for right now
        if (
            comm.category in ("f", "u")
            and comm.foia.email
            and comm.foia.email.status == "good"
            and comm.foia.user.is_staff
        ):
            subject, msg_id = self._set_reply_fields(comm)
            if subject is None:
                super().send_msg(comm, **kwargs)
                return
            comm.subject = subject
            comm.save()
            headers = {"In-Reply-To": f"<{msg_id}>"}
            comm.foia.send_email(comm, headers=headers, **kwargs)
        else:
            super().send_msg(comm, **kwargs)

    def _set_reply_fields(self, comm):
        """Try to find an appropriate message to reply to"""
        for communication in comm.foia.communications.filter(response=True).order_by(
            "-datetime"
        ):
            # GovQA expects the tracking ID after two colons, so try to find a
            # message in that format to reply to
            if "::" in communication.subject:
                subject = f"RE: {communication.subject}"
                if len(subject) > 255:
                    return None, None
                email = communication.emails.last()
                if email is None or not email.message_id:
                    return None, None
                return subject, email.message_id

        return None, None

    def get_client(self, comm):
        """Get a GovQA client"""
        url = furl(comm.foia.portal.url).origin
        logger.info(
            "[GOVQA] FOIA: %d Comm: %d - Getting Client from %s",
            comm.foia_id,
            comm.pk,
            url,
        )
        client = GovQA(url, check_login=False)
        logger.info("[GOVQA] FOIA: %d Comm: %d - Logging In", comm.foia_id, comm.pk)
        client.login(comm.foia.get_request_email(), comm.foia.portal_password)
        logger.info(
            "[GOVQA] FOIA: %d Comm: %d - Returning Client", comm.foia_id, comm.pk
        )
        return client

    def receive_msg(self, comm, **kwargs):
        """Check for attachments upon receiving a communication"""
        super().receive_msg(comm, **kwargs)
        if not self.portal.disable_automation:
            portal_task.delay(self.portal.pk, "receive_msg_task", [comm.pk], kwargs)

    def _get_request(self, client, comm):
        """Get the correct request for receive msg task"""
        logger.warning(
            "[GOVQA] FOIA: %d Comm: %d - Listing requests",
            comm.foia_id,
            comm.pk,
        )
        reqs = client.list_requests()

        if len(reqs) == 0:
            logger.warning(
                "[GOVQA] FOIA: %d Comm: %d, list_requests returned no requests",
                comm.foia_id,
                comm.pk,
            )
            return None

        for request in reqs:
            # find the request with a matching reference number
            # if none match, take the last one
            if request["reference_number"] == comm.foia.current_tracking_id():
                break
        else:
            request = reqs[-1]

        request_id = request["id"]
        request = client.get_request(request_id)
        logger.info(
            "[GOVQA] FOIA %d Comm: %d Request %s", comm.foia_id, comm.pk, request
        )

        return request

    def _get_attachments(self, request, comm):
        """Get the correct request for receive msg task"""
        logger.info(
            "[GOVQA] FOIA: %d Comm: %d - Getting attachments",
            comm.foia_id,
            comm.pk,
        )

        # We want to find the previous message from the same sender as the most recent
        # message.  The most recent message is at index 0.
        replier = request["messages"][0]["sender"]
        for message in request["messages"][1:]:
            if message["sender"] == replier:
                break
        else:
            message = None

        if message is None:
            # if this is the first reply, grab all attachments
            upload_attachments = request["attachments"]
        else:
            # get all attachments since the previous reply
            date = dateutil.parser.parse(message["date"]).date()
            upload_attachments = [
                a for a in request["attachments"] if a["uploaded_at"] > date
            ]

        logger.info(
            "[GOVQA] FOIA: %d Comm: %d - Attachments: %s",
            comm.foia_id,
            comm.pk,
            upload_attachments,
        )
        return upload_attachments

    def receive_msg_task(self, comm_pk, **kwargs):
        """Fetch the request from GovQA"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        try:
            logger.warning(
                "[GOVQA] FOIA: %d Comm: %d - Start",
                comm.foia_id,
                comm_pk,
            )
            client = self.get_client(comm)

            request = self._get_request(client, comm)
            if request is None:
                return

            upload_attachments = self._get_attachments(request, comm)

            for attachment in upload_attachments:
                value, params = parse_header(attachment["content-disposition"])
                if value == "attachment" and "filename" in params:
                    file_name = params["filename"]
                else:
                    logger.warning(
                        "[GOVQA] FOIA: %d Comm: %d - No file name for attachment: %s",
                        comm.foia_id,
                        comm_pk,
                        attachment,
                    )
                    continue

                portal_task.delay(
                    self.portal.pk,
                    "download_attachment_task",
                    [comm.pk, attachment["url"], file_name],
                    kwargs,
                )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "[GOVQA] FOIA: %d Comm: %d - Error: %s",
                comm.foia_id,
                comm_pk,
                exc,
                exc_info=sys.exc_info(),
            )
            FlaggedTask.objects.create(
                text=f"Error during GovQA scraping: {exc}",
                foia_id=comm.foia_id,
                category="govqa",
            )

    def download_attachment_task(self, comm_pk, url, file_name, **kwargs):
        """Download individual attachments"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        try:
            logger.info(
                "[GOVQA] FOIA: %s Comm: %d - Downloading: %s %s",
                comm.foia_id,
                comm_pk,
                url,
                file_name,
            )

            # stream the download to not overflow RAM on large files
            with requests.get(url, stream=True, timeout=10) as resp:
                if resp.status_code != 200:
                    logger.warning(
                        "[GOVQA] Communication: %d Download failed: %s %s Status: %d "
                        "Error: %s",
                        comm_pk,
                        url,
                        file_name,
                        resp.status_code,
                        resp.text,
                    )
                    return
                path = get_path(file_name)
                full_path = f"s3://{settings.AWS_MEDIA_BUCKET_NAME}/{path}"
                with smart_open(
                    full_path, "wb", s3_upload={"ACL": "public-read"}
                ) as file:
                    for chunk in resp.iter_content(chunk_size=10 * 1024 * 1024):
                        file.write(chunk)

            logger.info(
                "[GOVQA] FOIA: %d Comm: %d - Download complete: %s %s",
                comm.foia_id,
                comm_pk,
                url,
                file_name,
            )
            comm.attach_file(path=path, name=file_name)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "[GOVQA] FOIA: %d Comm: %d Download Attachment: %s - Error: %s",
                comm.foia_id,
                comm_pk,
                file_name,
                exc,
                exc_info=sys.exc_info(),
            )
            FlaggedTask.objects.create(
                text=f"Error during GovQA scraping: {exc}",
                foia_id=comm.foia_id,
                category="govqa",
            )
