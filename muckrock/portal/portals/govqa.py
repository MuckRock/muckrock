"""
Automate some parts of GovQA portal handling
"""


# Django
from django.conf import settings

# Standard Library
import cgi
import logging

# Third Party
import dateutil
import requests
from furl import furl
from govqa.base import GovQA
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.models.file import get_path
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task

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
        client = GovQA(
            furl(comm.foia.portal.url).origin,
            check_login=False,
        )
        client.login(comm.foia.get_request_email(), comm.foia.portal_password)
        return client

    def receive_msg(self, comm, **kwargs):
        """Check for attachments upon receiving a communication"""
        super().receive_msg(comm, **kwargs)
        if not self.portal.disable_automation:
            portal_task.delay(self.portal.pk, "receive_msg_task", [comm.pk], kwargs)

    def _get_request(self, client, comm):
        """Get the correct request for receive msg task"""
        reqs = client.list_requests()

        if len(reqs) == 0:
            logger.warning(
                "[GOVQA] Communication: %d, list_requests returned no requests",
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
        logger.info("[GOVQA] Communication: %d Request %s", comm.pk, request)

        return request

    def _get_attachments(self, request, comm):
        """Get the correct request for receive msg task"""

        # the requestor is the original sender - we went all replies,
        # which are messages sent by not the requestor
        requester = request["messages"][-1]["sender"]
        replies = [m for m in request["messages"] if m["sender"] != requester]

        if len(replies) < 2:
            # if this is the first reply, grab all attachments
            upload_attachments = request["attachments"]
        else:
            # get all attachments since the previous reply
            date = dateutil.parser.parse(replies[1]["date"]).date()
            upload_attachments = [
                a for a in request["attachments"] if a["uploaded_at"] >= date
            ]

        logger.info(
            "[GOVQA] Communication: %d Attachments: %s", comm.pk, upload_attachments
        )
        return upload_attachments

    def receive_msg_task(self, comm_pk, **kwargs):
        """Fetch the request from GovQA"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        client = self.get_client(comm)

        request = self._get_request(client, comm)
        if request is None:
            return

        upload_attachments = self._get_attachments(request, comm)

        for attachment in upload_attachments:
            value, params = cgi.parse_header(attachment["content-disposition"])
            if value == "attachment" and "filename" in params:
                file_name = params["filename"]
            else:
                logger.warning(
                    "[GOVQA] Communication: %d No file name for attachment: %s",
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

    def download_attachment_task(self, comm_pk, url, file_name, **kwargs):
        """Download individual attachments"""
        logger.info(
            "[GOVQA] Communication: %d Downloading: %s %s", comm_pk, url, file_name
        )
        comm = FOIACommunication.objects.get(pk=comm_pk)

        # stream the download to not overflow RAM on large files
        with requests.get(url, stream=True) as resp:
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
            with smart_open(full_path, "wb", s3_upload={"ACL": "public-read"}) as file:
                for chunk in resp.iter_content(chunk_size=10 * 1024 * 1024):
                    file.write(chunk)

        logger.info(
            "[GOVQA] Communication: %d Download complete: %s %s",
            comm_pk,
            url,
            file_name,
        )
        comm.attach_file(path=path, name=file_name)
