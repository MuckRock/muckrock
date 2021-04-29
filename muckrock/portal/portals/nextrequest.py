# -*- coding: utf-8 -*-
"""
Logic for interacting with NextRequest portals automatically
"""

# Django
from django.conf import settings
from django.template.defaultfilters import linebreaks
from django.utils import timezone

# Standard Library
import json
import re
import time
from datetime import datetime

# Third Party
import requests
from bs4 import BeautifulSoup
from furl import furl

# MuckRock
from muckrock.communication.models import PortalCommunication
from muckrock.foia.models import FOIACommunication
from muckrock.foia.tasks import prepare_snail_mail
from muckrock.portal.exceptions import PortalError
from muckrock.portal.portals.automated import PortalAutoReceiveMixin
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task
from muckrock.task.models import PortalTask


class NextRequestPortal(PortalAutoReceiveMixin, ManualPortal):
    """NextRequest Portal integration"""

    router = [
        (
            r"Your first record request (?P<tracking_id>[0-9-]+) "
            r"has been opened[.]",
            "confirm_open",
        ),
        (
            r"\[(?:ACTION REQUIRED|Action Required)\] Confirm your .* portal account",
            "confirm_account",
        ),
        (r"\[External Message Added\]", "text_reply"),
        (
            r"(?:\[Document Released to Requester\]|\[Document Released\])",
            "document_reply",
        ),
        (
            r"public records request (?:[0-9-]+) "
            r"has been (?P<status>closed|published|reopened)[.]",
            "status_update",
        ),
        (r"\[Department Changed\]", "dept_change"),
        (r"\[Due Date Changed\]", "due_date_change"),
    ]

    # sending

    def send_msg(self, comm, **kwargs):
        """Send a message to the NextRequest portal"""
        # need to update communications to ensure we have the correct count
        # for figuring out if this is a new or update message
        comm.foia.communications.update()
        category, extra = comm.foia.process_manual_send(**kwargs)

        if category == "n":
            portal_task.delay(self.portal.pk, "send_new_msg_task", [comm.pk], kwargs)
        elif category in ("f", "u"):
            portal_task.delay(
                self.portal.pk, "send_followup_msg_task", [comm.pk], kwargs
            )
        elif category == "p":
            # Payments are still always mailed
            prepare_snail_mail.delay(comm.pk, category, False, extra)
        else:
            super(NextRequestPortal, self).send_msg(
                comm, reason="Unknown category of send message", **kwargs
            )

    def send_new_msg_task(self, comm_pk, **kwargs):
        """Send an initial request as a task"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        try:
            foia = comm.foia
            user = foia.user
            email = foia.get_request_email()
            password = self.get_new_password()

            session = requests.Session()
            csrf_token = self._get_csrf_token(session, "requests/new")

            data = {
                "request[subtitle]": "",  # this must be blank
                "request[request_text]": linebreaks(comm.communication),
                "requester[email]": email,
                "requester[name]": user.profile.full_name,
                "requester[phone_number]": settings.PHONE_NUMBER,
                "requester[address]": f"{settings.ADDRESS_DEPT}, "
                "{settings.ADDRESS_STREET}".format(pk=foia.pk),
                "requester[city]": settings.ADDRESS_CITY,
                "requester[state]": settings.ADDRESS_STATE,
                "requester[zipcode]": settings.ADDRESS_ZIP,
                "requester[company]": "",
                "utf8": "✓",
                "authenticity_token": csrf_token,
                "commit": "Make Request",
            }
            # this doesn't work without this 4 second delay here
            time.sleep(4)
            reply = self._post(
                session,
                furl(self.portal.url).add(path="requests").url,
                "Making the initial request",
                data=data,
            )
            csrf_token = self._get_csrf_token(reply=reply)

            data = {
                "user[email]": email,
                "user[password]": password,
                "user[password_confirmation]": password,
                "utf8": "✓",
                "authenticity_token": csrf_token,
                "commit": "Save",
            }
            self._post(
                session,
                furl(self.portal.url).add(path="passwords").url,
                "Saving the password",
                data=data,
            )
            foia.status = "ack"
            foia.portal_password = password
            foia.save()
            PortalCommunication.objects.create(
                communication=comm,
                sent_datetime=timezone.now(),
                portal=self.portal,
                direction="outgoing",
            )
        except PortalError as exc:
            # if we have any problems sending the message, fall back to a
            # manual send, with an error message explaining what went wrong
            super(NextRequestPortal, self).send_msg(comm, reason=exc.args[0], **kwargs)

    def send_followup_msg_task(self, comm_pk, **kwargs):
        """Send a followup message as a task"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        try:
            request_id = self._get_request_id(comm)
            session = requests.Session()
            self._login(comm, session)
            csrf_token = self._get_csrf_token(
                session, ["requests", comm.foia.current_tracking_id()]
            )
            headers = {"X-CSRF-Token": csrf_token, "X-Requested-With": "XMLHttpRequest"}
            data = {
                "note[note_text]": linebreaks(comm.communication),
                "note[request_id]": request_id,
                "type": "external",
            }
            self._post(
                session,
                furl(self.portal.url).add(path="notes").url,
                "Sending a followup message",
                data=data,
                headers=headers,
            )
            self._send_documents(comm, session, request_id)
            PortalCommunication.objects.create(
                communication=comm,
                sent_datetime=timezone.now(),
                portal=self.portal,
                direction="outgoing",
            )
        except PortalError as exc:
            # if we have any problems sending the message, fall back to a
            # manual send, with an error message explaining what went wrong
            super(NextRequestPortal, self).send_msg(comm, reason=exc.args[0], **kwargs)

    def _get_request_id(self, comm):
        """Get the request id for sending followup messages"""
        if not comm.foia:
            raise PortalError("Communication has no FOIA\n" "Fetching Request ID")
        if not comm.foia.current_tracking_id():
            raise PortalError("FOIA has no tracking ID\n" "Fetching Request ID")
        pattern = re.compile("[0-9]+-([0-9]+)")
        match = pattern.match(comm.foia.current_tracking_id())
        if not match:
            raise PortalError(
                "FOIA tracking ID not in expected format\n" "Fetching Request ID"
            )
        return match.groups(1)

    def _send_documents(self, comm, session, request_id):
        """Send a document along with a request or followup"""
        # pylint: disable=too-many-locals
        csrf_token = self._get_csrf_token(
            session, ["requests", comm.foia.current_tracking_id()]
        )
        documents = []
        for file_ in comm.files.all():
            params = {
                "filename": file_.name(),
                "request_id": request_id,
                "xhr_upload": "true",
            }
            reply = self._get(
                session,
                furl(self.portal.url).add(path="presigned_url").url,
                "Signing a document for upload",
                params=params,
            )
            reply_json = reply.json()
            data = json.loads(reply_json["formData"])
            files = {"file": (file_.name(), file_.ffile)}
            reply = self._post(
                session,
                reply_json["url"],
                "Upload the document",
                data=data,
                files=files,
                expected_status=201,
            )
            location_pattern = re.compile(r"<Location>https?:([^<]+)</Location>")
            match = location_pattern.search(reply.content)
            if not match:
                raise PortalError(
                    "While uploading documents\n" "Could not parse location from XML"
                )
            location = match.group(1).replace("%2F", "/")
            documents.append((file_.name(), location))

        headers = {"X-CSRF-Token": csrf_token, "X-Requested-With": "XMLHttpRequest"}
        data = {"request_id": request_id}
        for i, (name, location) in enumerate(documents):
            data["documents[{}][description]".format(i)] = ""
            data["documents[{}][url]".format(i)] = location
            data["documents[{}][title]".format(i)] = name
            data["documents[{}][filename]".format(i)] = name
            data["documents[{}][doc_date]".format(i)] = ""
        self._post(
            session,
            furl(self.portal.url).add(path="documents").url,
            "Saving the uploaded documents",
            data=data,
            headers=headers,
        )

    # receiving

    def confirm_open(self, comm, tracking_id):
        """Receive a confirmation that the request was created"""

        def on_match(match):
            """Set metadata and unhide the communication"""
            comm.foia.status = "processed"
            comm.foia.add_tracking_id(tracking_id)
            comm.foia.save()
            comm.communication = match.group("communication")
            comm.hidden = False
            comm.save()
            PortalCommunication.objects.create(
                communication=comm,
                sent_datetime=timezone.now(),
                portal=self.portal,
                direction="incoming",
            )

        self._process_msg(
            comm=comm,
            regex=r"Write ABOVE THIS LINE.*"
            r"(?P<communication>Your first .*)"
            r"As the requester",
            on_match=on_match,
            error_reason="Could not extract the created message",
        )

    def confirm_account(self, comm):
        """Confirm our portal account"""

        def on_match(match):
            """Open the confirmation page"""
            portal_task.delay(
                self.portal.pk, "confirm_account_task", [comm.pk, match.group("link")]
            )

        self._process_msg(
            comm=comm,
            regex=r"Confirm your account \((?P<link>[^)]*)\)",
            on_match=on_match,
            error_reason="Could not find confirmation link",
        )

    def confirm_account_task(self, comm_pk, link):
        """Do the confirmation in a task"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        reply = requests.get(link)
        if reply.status_code == 200:
            # If there were initial files on the request,
            # they must be uploaded after confirming the account
            first_comm = comm.foia.communications.first()
            if first_comm.files.exists():
                try:
                    request_id = self._get_request_id(first_comm)
                    session = requests.Session()
                    self._login(first_comm, session)
                    self._send_documents(first_comm, session, request_id)
                except PortalError as exc:
                    PortalTask.objects.create(
                        category="u",
                        communication=first_comm,
                        reason="The request was successfully created but "
                        "the attachments were not successfully uploaded\n"
                        + exc.args[0],
                    )
            PortalCommunication.objects.create(
                communication=comm,
                sent_datetime=timezone.now(),
                portal=self.portal,
                direction="incoming",
            )
        else:
            ManualPortal.receive_msg(self, comm, reason="Confirmation link failed")

    def text_reply(self, comm):
        """Handle text replies"""

        def on_match(match):
            """Only show the message and unhide the communication"""
            self._accept_comm(comm, match.group("message"))

        self._process_msg(
            comm=comm,
            regex=r"A message was sent to you regarding record request #[^:]*:"
            r"(?P<message>.*?)View Request",
            on_match=on_match,
            error_reason="Could not extract the message",
        )

    def document_reply(self, comm):
        """Download documents from the portal"""

        def on_match(match):
            """Download the files"""
            if comm.foia.current_tracking_id() != match.group("tracking_id"):
                ManualPortal.receive_msg(
                    self, comm, reason="Tracking ID does not match"
                )
            portal_task.delay(
                self.portal.pk,
                "document_reply_task",
                [comm.pk, match.group("documents"), match.group("text")],
            )

        self._process_msg(
            comm=comm,
            regex=r"(?P<text>(?:A document has|Documents have) been released "
            r"(:?to you )?for record request\s#(?P<tracking_id>[0-9-]+):"
            r"(?P<documents>.*))View Request",
            on_match=on_match,
            error_reason="Could not find the file list",
        )

    def document_reply_task(self, comm_pk, documents, text):
        """Download the documents in a task"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        try:
            session = requests.Session()
            self._login(comm, session)
            reply = self._get(
                session,
                furl(self.portal.url)
                .add(path=["requests", comm.foia.current_tracking_id()])
                .url,
                "Getting request page to view list of documents",
            )
            documents = [d.strip("-* \r") for d in documents.split("\n") if d.strip()]
            soup = BeautifulSoup(reply.content, "lxml")
            for document in documents:
                href = self._find_tag_attr(
                    soup,
                    {"name": "a", "class": "document-link", "string": document},
                    "href",
                    "Attempting to find the document: {}".format(document),
                )
                url = furl(self.portal.url).add(path=href)
                reply = self._get(
                    session, url, "Downloading document: {}".format(document)
                )
                comm.attach_file(
                    content=reply.content, name=document, source=self.portal.name
                )
            self._accept_comm(comm, text)
        except PortalError as exc:
            ManualPortal.receive_msg(self, comm, reason=exc.args[0])

    def status_update(self, comm, status):
        """A status update message"""
        self._accept_comm(comm, "Your request has been {}.".format(status))

    def dept_change(self, comm):
        """Handle department change replies"""

        def on_match(match):
            """Only show the message and unhide the communication"""
            self._accept_comm(comm, match.group("message"))

        self._process_msg(
            comm=comm,
            regex=r"(?P<message>Department assignment for .*?)View Request",
            on_match=on_match,
            error_reason="Could not extract the message",
        )

    def due_date_change(self, comm):
        """Handle due date change replies"""

        def on_match(match):
            """Set the estimated completion date"""
            if comm.foia.current_tracking_id() != match.group("tracking_id"):
                ManualPortal.receive_msg(
                    self, comm, reason="Tracking ID does not match"
                )
            try:
                comm.foia.date_estimate = datetime.strptime(
                    match.group("date"), "%B %d, %Y"
                ).date()
            except ValueError:
                ManualPortal.receive_msg(
                    self, comm, reason="Bad date: {}".format(match.group("date"))
                )
            else:
                comm.foia.save()
                self._accept_comm(comm, match.group("message"))

        self._process_msg(
            comm=comm,
            regex=r"(?P<message>The due date for record request"
            r"\s#(?P<tracking_id>[0-9-]+)\shas been changed to: "
            r"(?P<date>[A-Za-z]+ [0-9]{1,2}, [0-9]{4}))",
            on_match=on_match,
            error_reason="Could not find the due date",
        )

    def _process_msg(self, comm, regex, on_match, error_reason):
        """Process an incoming message based on a regex match of the content"""
        pattern = re.compile(regex, re.MULTILINE | re.DOTALL | re.UNICODE)
        match = pattern.search(comm.communication)
        if match:
            on_match(match)
        else:
            ManualPortal.receive_msg(self, comm, reason=error_reason)

    def _get_csrf_token(self, session=None, path="", reply=None):
        """Get the CSRF token from the given path or reply"""
        if session is not None:
            url = furl(self.portal.url).add(path=path)
            reply = self._get(session, url, "Attempting to get CSRF token")
        soup = BeautifulSoup(reply.content, "lxml")
        return self._find_tag_attr(
            soup,
            {"name": "meta", "attrs": {"name": "csrf-token"}},
            "content",
            "Attempting to get CSRF token",
        )

    def _login(self, comm, session):
        """Login to the portal"""
        csrf_token = self._get_csrf_token(session, "users/sign_in")
        data = {
            "user[email]": comm.foia.get_request_email(),
            "user[password]": comm.foia.portal_password,
            "user[remember_me]": 0,
            "utf8": "✓",
            "authenticity_token": csrf_token,
            "commit": "Sign In",
        }
        reply = self._post(
            session,
            furl(self.portal.url).add(path="users/sign_in"),
            "Logging in",
            data=data,
        )
        soup = BeautifulSoup(reply.content, "lxml")
        tag = soup.find("span", class_="notice", text="Signed in successfully.")
        if tag is None:
            raise PortalError("Error logging in")

    def _request(self, type_, session, url, msg, expected_status=200, **kwargs):
        """Make a request and check the status code"""
        # pylint: disable=too-many-arguments
        method = getattr(session, type_)
        reply = method(url, **kwargs)
        if reply.status_code != expected_status:
            raise PortalError(
                "Error fetching: {url}\n"
                "Status code: {code}\n"
                "{msg}".format(url=url, code=reply.status_code, msg=msg)
            )
        return reply

    def _get(self, session, url, msg, expected_status=200, **kwargs):
        """Make a get request with error handling"""
        # pylint: disable=too-many-arguments
        return self._request("get", session, url, msg, expected_status, **kwargs)

    def _post(self, session, url, msg, expected_status=200, **kwargs):
        """Make a post request with error handling"""
        # pylint: disable=too-many-arguments
        return self._request("post", session, url, msg, expected_status, **kwargs)

    def _find_tag_attr(self, soup, find_kwargs, attr_name, msg):
        """Use BS to find a tag's attribute in the html"""
        tag = soup.find(**find_kwargs)
        if not tag:
            raise PortalError(
                "Error finding tag: {args}\n" "{msg}".format(args=find_kwargs, msg=msg)
            )
        attr = tag.attrs.get(attr_name)
        if not attr:
            raise PortalError(
                "Error finding attr: {attr}\n"
                "Tag: {tag}\n"
                "{msg}".format(attr=attr_name, tag=tag, msg=msg)
            )
        return attr
