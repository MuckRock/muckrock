# -*- coding: utf-8 -*-
"""
Logic for interacting with FBI portals automatically
"""

# Django
from django.utils import timezone

# Standard Library
import logging
import os
import re
import time

# Third Party
import requests
import sentry_sdk

# MuckRock
from muckrock.communication.models import PortalCommunication
from muckrock.core.utils import requests_retry_session
from muckrock.foia.models import FOIACommunication, RawEmail
from muckrock.portal.portals.automated import PortalAutoReceiveMixin
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task

FBI_PORTAL_EMAIL = os.environ.get("FBI_PORTAL_EMAIL", "")
FBI_DOWNLOAD_DELAY = int(os.environ.get("FBI_DOWNLOAD_DELAY", "5"))
# transient-failure retry budget for reading the raw-email body from S3
FBI_BODY_MAX_RETRIES = int(os.environ.get("FBI_BODY_MAX_RETRIES", "5"))
FBI_BODY_RETRY_DELAY = int(os.environ.get("FBI_BODY_RETRY_DELAY", "30"))

logger = logging.getLogger(__name__)


class FBIPortal(PortalAutoReceiveMixin, ManualPortal):
    """FBI eFOIPA Portal integration"""

    router = [
        (r"eFOIA Request Received", "confirm_open"),
        (r"eFOIA files available", "document_reply"),
    ]

    def get_new_password(self):
        """The FBI portal does not use a password"""
        return ""

    def confirm_open(self, comm):
        """Confirm receipt of request"""
        comm.foia.status = "processed"
        comm.foia.save()
        PortalCommunication.objects.create(
            communication=comm,
            sent_datetime=timezone.now(),
            portal=self.portal,
            direction="incoming",
        )

    def document_reply(self, comm):
        """Process incoming documents"""
        p_file_available = re.compile(
            r"There are eFOIA files available for you to download"
        )
        match = p_file_available.search(comm.communication)
        if match:
            portal_task.delay(self.portal.pk, "document_reply_task", [comm.pk])
        else:
            ManualPortal.receive_msg(self, comm, reason="Unexpected email format")

    def _raw_email_body(self, comm):
        """Return the body containing the download links and per-file tokens.

        The full body is present in the raw email's text/plain part.
        Inbound ingest (muckrock/mailgun/views.py) stores Mailgun's
        stripped-text into comm.communication, which unreliably strips the
        FBI's link/token bullets. Communication is sometimes the full
        body and sometimes just the intro line. Prefer communication when it
        actually contains the tokens. Only then fall back to the raw email
        (an S3 read that can be transiently empty right after delivery).
        """
        if "Use this token to access" in (comm.communication or ""):
            return comm.communication
        email_comm = comm.emails.first()
        if email_comm is None:
            return None
        try:
            text, _html = email_comm.rawemail.get_text_html()
        except RawEmail.DoesNotExist:
            return None
        return text or None

    def document_reply_task(self, comm_pk, attempt=0):
        """Download the documents asynchronously"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        body = self._raw_email_body(comm)
        if body is None:
            # The body may only live in the raw email's text/plain part, which
            # is stored in S3. Right after delivery that object may not be
            # readable yet, and RawEmail.raw_email is an mproperty, so
            # an empty read gets memoized for the life of the worker instance.
            if attempt < FBI_BODY_MAX_RETRIES:
                portal_task.apply_async(
                    args=[
                        self.portal.pk,
                        "document_reply_task",
                        [comm_pk, attempt + 1],
                    ],
                    countdown=FBI_BODY_RETRY_DELAY,
                )
                return
            self._report_broken(comm, "Could not read text/plain from raw email")
            return

        # Each file link is followed by a per-file token, and the download URL
        # is a token-gated page. POST the token to the URL to get the bytes.
        p_document = re.compile(
            r"\* \[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)"
            r"\s*\* Use this token to access:\s*(?P<token>\S+)"
        )
        # Every link should pair with a token; if not, the format changed again.
        p_link_only = re.compile(r"\* \[[^\]]+\]\([^)]+\)")
        matches = list(p_document.finditer(body))
        if len(matches) != len(p_link_only.findall(body)):
            self._report_broken(comm, "Could not pair every file link with a token")
            return

        # skip files already attached so a rerun doesn't duplicate them.
        # attach_file stores the extension-stripped basename as `title`, so
        # compare against the same transform to match already-attached files.
        existing = set(comm.files.values_list("title", flat=True))

        # retries 429/5xx with exponential backoff at the adapter layer.
        # The tokens are valid for 48 hours, so retrying the POST is safe.
        # POST must be added to allowed_methods because urllib3's default
        # frozenset excludes it (POSTs are not retried by default).
        session = requests_retry_session(
            retries=5, backoff_factor=2, allowed_methods=frozenset({"POST"})
        )

        for i, match in enumerate(matches):
            name = match.group("name")
            title = os.path.splitext(name)[0][:255]
            if title in existing:
                continue
            if i > 0:
                # space out requests proactively to avoid FBI rate limiting
                time.sleep(FBI_DOWNLOAD_DELAY)
            if not self._download_file(comm, session, match):
                return
        self._accept_comm(comm, "There are eFOIA files available for you to download.")

    def _download_file(self, comm, session, match):
        """POST the token and attach the file. Returns True on success, or
        reports the failure to manual review and returns False."""
        name = match.group("name")
        url = match.group("url")
        token = match.group("token")
        try:
            reply = session.post(
                url,
                data={"token": token, "download": "Download File"},
                timeout=10,
            )
        except requests.RequestException as exc:
            # exhausted retries or a non-retryable network error
            self._report_broken(
                comm, "Download failed after retries: {} ({})".format(name, exc)
            )
            return False

        if reply.status_code != 200:
            self._report_broken(
                comm,
                "Error downloading file: {} (status {})".format(
                    name, reply.status_code
                ),
            )
            return False
        # A wrong/expired token re-renders the HTML gate with a 200
        # This is a guard against saving the page instead of the file.
        content_type = reply.headers.get("Content-Type", "").lower()
        if "text/html" in content_type:
            self._report_broken(
                comm, "Token gate returned instead of a file: {}".format(name)
            )
            return False
        comm.attach_file(content=reply.content, name=name, source=self.portal.name)
        return True

    def _report_broken(self, comm, reason):
        """Route to manual review and alert that the automation is broken"""
        logger.error("FBI portal automation failed: %s (comm %d)", reason, comm.pk)
        sentry_sdk.capture_message(
            "FBI portal automation failed: {} (comm {})".format(reason, comm.pk),
            level="error",
        )
        ManualPortal.receive_msg(self, comm, reason=reason)

    def send_msg(self, comm, **kwargs):
        """Send a message via email if it is not a new submission"""
        # need to update communications to ensure we have the correct count
        # for figuring out if this is a new or update message
        comm.foia.communications.update()
        comm.foia.process_manual_send(**kwargs)

        if comm.category in ("f", "u"):
            # send to default email address if we do not have one on file or
            # if the last reply was from the portal email address
            if comm.foia.email is None or comm.foia.email.email == FBI_PORTAL_EMAIL:
                comm.foia.email = comm.foia.agency.get_emails("primary", "to").first()
                comm.foia.save()
            if comm.foia.email and comm.foia.email.status == "good":
                # do not send email to bad email addresses
                comm.foia.send_email(comm, **kwargs)
            else:
                super().send_msg(comm, **kwargs)
        else:
            super().send_msg(comm, **kwargs)
