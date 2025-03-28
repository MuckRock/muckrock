# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

# Django
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils import timezone

# Standard Library
import logging
import mimetypes
import os
import re
from email import policy
from email.parser import BytesParser

# Third Party
import chardet
from memoize import mproperty

# MuckRock
from muckrock.core.storage import PrivateMediaRootS3BotoStorage
from muckrock.core.utils import UnclosableFile, new_action
from muckrock.foia.models.file import FOIAFile
from muckrock.foia.models.request import STATUS, FOIARequest
from muckrock.foia.querysets import FOIACommunicationQuerySet, RawEmailQuerySet
from muckrock.task.constants import SNAIL_MAIL_CATEGORIES

logger = logging.getLogger(__name__)

DELIVERED = (("fax", "Fax"), ("email", "Email"), ("mail", "Mail"), ("web", "Web"))


class FOIACommunication(models.Model):
    """A single communication of a FOIA request"""

    foia = models.ForeignKey(
        FOIARequest,
        related_name="communications",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    from_user = models.ForeignKey(
        "auth.User",
        related_name="sent_communications",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    to_user = models.ForeignKey(
        "auth.User",
        related_name="received_communications",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    subject = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="The subject line for this communication",
    )
    datetime = models.DateTimeField(
        db_index=True,
        help_text="Timestamp for when this communication was sent",
    )

    response = models.BooleanField(
        default=False,
        help_text="Is this a response (or a request)?",
    )

    autogenerated = models.BooleanField(
        default=False,
        help_text="Was this communication automatically generated by MuckRock",
    )
    thanks = models.BooleanField(default=False)
    full_html = models.BooleanField(default=False)
    communication = models.TextField(
        blank=True,
        help_text="The body text of the communication",
    )
    hidden = models.BooleanField(default=False)
    download = models.BooleanField(
        default=False, help_text="This communication has pending files to download"
    )

    # what status this communication should set the request to - used for
    # machine learning
    status = models.CharField(
        max_length=12,
        choices=STATUS,
        blank=True,
        null=True,
        help_text="The status the request was set to for this communication",
    )
    category = models.CharField(
        max_length=1,
        choices=SNAIL_MAIL_CATEGORIES,
        blank=True,
    )

    # only used for orphans
    likely_foia = models.ForeignKey(
        FOIARequest,
        related_name="likely_communications",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Depreacted fields
    # keep these for old communications
    from_who = models.CharField(max_length=255, blank=True)
    to_who = models.CharField(max_length=255, blank=True)
    priv_from_who = models.CharField(max_length=255, blank=True)
    priv_to_who = models.CharField(max_length=255, blank=True)

    # these can be deleted eventually
    delivered = models.CharField(
        max_length=10, choices=DELIVERED, blank=True, null=True
    )
    fax_id = models.CharField(max_length=10, blank=True, default="")
    confirmed = models.DateTimeField(blank=True, null=True)
    opened = models.BooleanField(
        default=False,
        help_text="DEPRECATED: If emailed, did we receive an open notification?"
        " If faxed, did we recieve a confirmation?",
    )

    objects = FOIACommunicationQuerySet.as_manager()

    def __str__(self):
        return "%s - %s" % (self.datetime, self.subject)

    def get_absolute_url(self):
        """The url for this object"""
        if self.foia:
            return self.foia.get_absolute_url() + ("#comm-%d" % self.pk)
        else:
            return ""

    def save(self, *args, **kwargs):
        """Remove controls characters from text before saving"""
        remove_control = dict.fromkeys(
            list(range(0, 9)) + list(range(11, 13)) + list(range(14, 32))
        )
        self.communication = str(self.communication).translate(remove_control)
        # limit communication length to 150k
        self.communication = self.communication[:150000]
        # special handling for certain agencies
        self._presave_special_handling()
        # update foia's date updated if this is the latest communication
        if self.foia and (
            self.foia.datetime_updated is None
            or self.datetime > self.foia.datetime_updated
        ):
            self.foia.datetime_updated = self.datetime
            self.foia.save(comment="update datetime_updated due to new comm")
        super().save(*args, **kwargs)

    def anchor(self):
        """Anchor name"""
        return "comm-%d" % self.pk

    def get_source(self):
        """Get the source line for an attached file"""
        if self.foia and self.foia.agency:
            return f"{self.foia.agency.name}, {self.foia.agency.jurisdiction}"
        elif self.from_user:
            return self.from_user.profile.full_name
        else:
            return ""

    def move(self, foia_pks, user):
        """
        Move this communication. If more than one foia_pk is given, move the
        communication to the first request, then clone it across the rest of
        the requests. Returns the moved and cloned communications.
        """
        # avoid circular imports
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.foia.tasks import upload_document_cloud

        foias = FOIARequest.objects.filter(pk__in=foia_pks)
        if not foias:
            raise ValueError("Expected a request to move the communication to.")
        old_foia = self.foia
        self.foia = foias[0]

        with transaction.atomic():
            for file_ in self.files.all():
                file_.source = self.get_source()
                file_.save()
                transaction.on_commit(
                    lambda file_=file_: upload_document_cloud.delay(file_.pk)
                )
            self.save()
            CommunicationMoveLog.objects.create(
                communication=self, foia=old_foia, user=user
            )
        logger.info("Communication #%d moved to request #%d", self.id, self.foia.id)
        # if cloning happens, self gets overwritten. so we save it to a variable here
        comm = FOIACommunication.objects.get(pk=self.pk)
        moved = [comm]
        cloned = []
        if foias[1:]:
            cloned = self.clone(foias[1:], user)
        return moved + cloned

    @transaction.atomic
    def clone(self, foias, user):
        """
        Copies the communication to each request in the list,
        then returns all the new communications.
        ---
        When setting self.pk to None and then calling self.save(),
        Django will clone the communication along with all of its data
        and give it a new primary key. On the next iteration of the loop,
        the clone will be cloned along with its data, and so on. Same thing
        goes for each file attached to the communication.
        """
        if not foias:
            raise ValueError("No valid request(s) provided for cloning.")
        cloned_comms = []
        original_pk = self.pk
        files = self.files.all()
        emails = self.emails.all()
        faxes = self.faxes.all()
        mails = self.mails.all()
        web_comms = self.web_comms.all()
        for foia in foias:
            clone = FOIACommunication.objects.get(pk=original_pk)
            clone.pk = None
            clone.foia = foia
            clone.save()
            CommunicationMoveLog.objects.create(
                communication=clone, foia=self.foia, user=user
            )
            for file_ in files:
                file_.clone(clone)
            # clone all sub communications as well
            for comms in [emails, faxes, mails, web_comms]:
                for comm in comms:
                    comm.pk = None
                    comm.communication = clone
                    comm.save()
            # for each clone, self gets overwritten. each clone needs to be
            # stored explicitly.
            cloned_comms.append(clone)
            logger.info(
                "Communication #%d cloned to request #%d", original_pk, clone.foia.id
            )
        return cloned_comms

    def make_sender_primary_contact(self):
        """Makes the communication's sender the primary contact of its FOIA."""
        if not self.foia:
            raise ValueError(
                "Communication is an orphan and has no associated request."
            )

        muckrock_domains = (settings.MAILGUN_SERVER_NAME, "muckrock.com")
        email_comm = self.emails.first()
        if (
            email_comm
            and email_comm.from_email
            and email_comm.from_email.domain not in muckrock_domains
        ):
            self.foia.email = email_comm.from_email
            new_cc_emails = list(email_comm.to_emails.all()) + list(
                email_comm.cc_emails.all()
            )
            new_cc_emails = [
                e for e in new_cc_emails if e.domain not in muckrock_domains
            ]
            self.foia.cc_emails.set(new_cc_emails)
            self.foia.save(comment="update primary contact from comm")

    def _presave_special_handling(self):
        """Special handling before saving
        For example, strip out BoP excessive quoting"""

        def test_agency_name(name):
            """Match on agency name"""
            return self.foia and self.foia.agency and self.foia.agency.name == name

        def until_string(string):
            """Cut communication off after string"""

            def modify():
                """Run the modification on self.communication"""
                if string in self.communication:
                    idx = self.communication.index(string)
                    self.communication = self.communication[:idx]

            return modify

        special_cases = [
            # BoP: strip everything after '>>>'
            (test_agency_name("Bureau of Prisons"), until_string(">>>")),
            # Phoneix Police: strip everything after '_'*32
            (test_agency_name("Phoenix Police Department"), until_string("_" * 32)),
        ]

        for test, modify in special_cases:
            if test:
                modify()

    def process_attachments(self, files):
        """Given uploaded files, turn them into FOIAFiles attached to the comm"""

        ignore_types = [("application/x-pkcs7-signature", "p7s")]

        for file_ in files.values():
            if not any(
                file_.content_type == t or file_.name.endswith(s)
                for t, s in ignore_types
            ):
                self.attach_file(file_=file_)

    def create_agency_notifications(self):
        """Create the notifications for when an agency creates a new comm"""
        if self.foia and self.foia.agency:
            action = new_action(
                self.foia.agency,
                "sent a communication",
                action_object=self,
                target=self.foia,
            )
            self.foia.notify(action)
        if self.foia:
            self.foia.update(self.anchor())

    def attach_file(
        self, file_=None, content=None, path=None, name=None, source=None, now=True
    ):
        """Attach a file to this communication"""
        # must supply either:
        # * a file_
        # * content and name_
        # * path and name_ (for files already uploaded to s3)
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.foia.tasks import upload_document_cloud

        assert (
            (file_ is not None)
            or (content is not None and name is not None)
            or (path is not None and name is not None)
        )

        if file_ is None and content is not None:
            file_ = ContentFile(content)
        if name is None and file_ is not None:
            name = file_.name
        if source is None:
            source = self.get_source()

        title = os.path.splitext(name)[0][:255]
        with transaction.atomic():
            foia_file = FOIAFile(
                comm=self,
                title=title,
                datetime=timezone.now() if now else self.datetime,
                source=source,
            )
            if file_:
                name = name[:233].encode("ascii", "ignore").decode()
                foia_file.ffile.save(name, UnclosableFile(file_))
            else:
                foia_file.ffile.name = path
                foia_file.save()
            if self.foia:
                transaction.on_commit(lambda: upload_document_cloud.delay(foia_file.pk))
        return foia_file

    def attach_files_to_email(self, msg):
        """Attach all of this communications files to the email message"""
        for file_ in self.files.all():
            name = file_.name()
            content = file_.ffile.read()
            mimetype, _ = mimetypes.guess_type(name)
            if mimetype and mimetype.startswith("text/"):
                enc = chardet.detect(content)["encoding"]
                content = content.decode(enc)
            msg.attach(name, content)

    def get_raw_email(self):
        """Get the raw email associated with this communication, if there is one"""
        return RawEmail.objects.filter(email__communication=self).last()

    def from_line(self):
        """What to display for who this communication is from"""
        if self.from_user and self.from_user.profile.is_agency_user:
            return self.from_user.profile.agency.name
        elif self.from_user:
            return self.from_user.profile.full_name
        else:
            return self.from_who

    def get_subcomm(self):
        """Get the latest sub communication type"""
        # sort all types of comms by sent datetime,
        # and return the latest
        sorted_comms = sorted(
            list(self.emails.all())
            + list(self.faxes.all())
            + list(self.mails.all())
            + list(self.web_comms.all())
            + list(self.portals.all()),
            key=lambda x: x.sent_datetime,
            reverse=True,
        )
        if not sorted_comms:
            return None
        return sorted_comms[0]

    def get_delivered(self):
        """Get how this comm was delivered"""
        subcomm = self.get_subcomm()
        if subcomm:
            return subcomm.delivered
        else:
            return "none"

    # for the admin
    get_delivered.short_description = "delivered"

    def sent_to(self):
        """Who was this communication sent to?"""
        subcomm = self.get_subcomm()
        if subcomm:
            return subcomm.sent_to()
        else:
            return None

    def sent_from(self):
        """Who was this communication sent from?"""
        subcomm = self.get_subcomm()
        if subcomm:
            return subcomm.sent_from()
        else:
            return None

    def verified(self):
        """Was this communication verified?"""
        subcomm = self.get_subcomm()
        if subcomm:
            return subcomm.verified()
        else:
            return None

    def get_delivered_and_from(self):
        """Combine get_delivered and sent_from for performance reasons"""
        subcomm = self.get_subcomm()
        if subcomm:
            return (subcomm.delivered, subcomm.sent_from())
        else:
            return (None, None)

    def extract_tracking_id(self):
        """Try to extract a tracking number from this communication"""
        if self.foia.tracking_ids.exists():
            # do not try to extract a tracking ID if one is already set
            return
        patterns = [re.compile(r"Tracking Number:\s+([0-9a-zA-Z-]+)")]
        for pattern in patterns:
            match = pattern.search(self.communication)
            if match:
                tracking_id = match.group(1).strip()[:255]
                self.foia.add_tracking_id(tracking_id)
                logger.info(
                    "FOIA Tracking ID set: FOIA PK: %d - Comm PK: %d - "
                    "Tracking ID: %s",
                    self.foia.id,
                    self.id,
                    tracking_id,
                )
                break

    class Meta:
        ordering = ["datetime"]
        verbose_name = "FOIA Communication"
        app_label = "foia"


class RawEmail(models.Model):
    """The raw email text for a communication - stored seperately for performance"""

    # nullable during transition
    # communication is depreacted and should be removed
    communication = models.OneToOneField(
        FOIACommunication, null=True, on_delete=models.SET_NULL
    )
    email = models.OneToOneField(
        "communication.EmailCommunication", null=True, on_delete=models.CASCADE
    )
    raw_email_db = models.TextField(blank=True)
    raw_email_file = models.FileField(
        upload_to="raw_emails/%Y/%m/%d",
        storage=PrivateMediaRootS3BotoStorage(),
        blank=True,
    )

    objects = RawEmailQuerySet.as_manager()

    def __str__(self):
        return "Raw Email: %d" % self.pk

    @mproperty
    def raw_email(self):
        """Get the raw email content"""
        # check S3 first, preferred storage destination
        if self.raw_email_file:
            return self.raw_email_file.read().decode("utf8")
        else:
            return self.raw_email_db

    @raw_email.setter
    def raw_email(self, value):
        """Set the raw email value"""
        self.raw_email_file = ContentFile(value.encode("utf8"), name=f"{self.pk}.eml")

    def get_text_html(self):
        """Decode the text and html from this raw email"""
        msg = BytesParser(policy=policy.default).parsebytes(
            self.raw_email.encode("utf8")
        )
        text = self._get_body(msg, "plain")
        html = self._get_body(msg, "html")
        return text, html

    def _get_body(self, msg, type_):
        """Get the decoded body for the given type from the message"""
        body = msg.get_body(preferencelist=(type_))
        if body:
            return body.get_content()
        return ""

    class Meta:
        app_label = "foia"


class FOIANote(models.Model):
    """A private note on a FOIA request"""

    foia = models.ForeignKey(
        FOIARequest, related_name="notes", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        "auth.User", related_name="notes", null=True, on_delete=models.PROTECT
    )
    datetime = models.DateTimeField(auto_now_add=True)
    note = models.TextField()
    notify = models.BooleanField(default=False)

    def __str__(self):
        if self.author:
            user = self.author
        else:
            user = self.foia.user
        return "Note by %s on %s" % (user.profile.full_name, self.foia.title)

    class Meta:
        ordering = ["foia", "datetime"]
        verbose_name = "FOIA Note"
        app_label = "foia"


class CommunicationError(models.Model):
    """An error has occured delivering this communication"""

    # Depreacted
    communication = models.ForeignKey(
        FOIACommunication, related_name="errors", on_delete=models.CASCADE
    )
    date = models.DateTimeField()

    recipient = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    error = models.TextField(blank=True)
    event = models.CharField(max_length=10)
    reason = models.CharField(max_length=255)

    def __str__(self):
        return "CommunicationError: %s - %s" % (self.communication.pk, self.date)

    class Meta:
        ordering = ["date"]
        app_label = "foia"


class CommunicationOpen(models.Model):
    """A communication has been opened"""

    # Depreacted
    communication = models.ForeignKey(
        FOIACommunication, related_name="opens", on_delete=models.CASCADE
    )
    date = models.DateTimeField()

    recipient = models.EmailField()
    city = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=10)

    client_type = models.CharField(max_length=15)
    client_name = models.CharField(max_length=50)
    client_os = models.CharField(max_length=10, verbose_name="Client OS")

    device_type = models.CharField(max_length=10)
    user_agent = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=15, verbose_name="IP Address")

    def __str__(self):
        return "CommunicationOpen: %s - %s" % (self.communication.pk, self.date)

    class Meta:
        ordering = ["date"]
        app_label = "foia"


class CommunicationMoveLog(models.Model):
    """Track communications being moved to different requests"""

    communication = models.ForeignKey(FOIACommunication, on_delete=models.CASCADE)
    foia = models.ForeignKey(
        "foia.FOIARequest", blank=True, null=True, on_delete=models.CASCADE
    )
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.foia:
            foia = "FOIA {}".format(self.foia.pk)
        else:
            foia = "orphan"
        return "Comm {} moved from {} by {} on {}".format(
            self.communication.pk, foia, self.user.username, self.datetime
        )
