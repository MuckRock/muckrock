"""
Models for the Task application
"""
# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Case, Count, Max, When
from django.db.models.functions import Cast, Now
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import linebreaks, urlize

# Standard Library
import logging
from datetime import date
from itertools import groupby

# Third Party
import bleach
from zenpy import Zenpy
from zenpy.lib.api_objects import (
    Comment,
    Organization as ZenOrganization,
    Ticket,
    User as ZenUser,
)

# MuckRock
from muckrock.communication.models import Check, EmailAddress, PhoneNumber
from muckrock.core.models import ExtractDay
from muckrock.core.utils import zoho_get, zoho_post
from muckrock.foia.models import STATUS, FOIATemplate
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.message.email import TemplateEmail
from muckrock.message.tasks import support
from muckrock.portal.models import PORTAL_TYPES
from muckrock.task.constants import (
    FLAG_CATEGORIES,
    PORTAL_CATEGORIES,
    SNAIL_MAIL_CATEGORIES,
)
from muckrock.task.querysets import (
    CrowdfundTaskQuerySet,
    FlaggedTaskQuerySet,
    MultiRequestTaskQuerySet,
    NewAgencyTaskQuerySet,
    NewPortalTaskQuerySet,
    OrphanTaskQuerySet,
    PaymentInfoTaskQuerySet,
    PortalTaskQuerySet,
    ProjectReviewTaskQuerySet,
    ResponseTaskQuerySet,
    ReviewAgencyTaskQuerySet,
    SnailMailTaskQuerySet,
    StatusChangeTaskQuerySet,
    TaskQuerySet,
)

logger = logging.getLogger(__name__)

# pylint: disable=missing-docstring
# pylint: disable=too-many-lines

MR_NUMBER_FIELD = 1500004565182


class Task(models.Model):
    """A base task model for fields common to all tasks"""

    date_created = models.DateTimeField(auto_now_add=True)
    date_done = models.DateTimeField(blank=True, null=True)
    date_deferred = models.DateField(blank=True, null=True)
    resolved = models.BooleanField(default=False, db_index=True)
    assigned = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="assigned_tasks",
        on_delete=models.PROTECT,
    )
    resolved_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="resolved_tasks",
        on_delete=models.PROTECT,
    )
    form_data = models.JSONField(blank=True, null=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ["date_created"]

    def __str__(self):
        return "Task"

    def resolve(self, user=None, form_data=None):
        """Resolve the task"""
        self.resolved = True
        self.resolved_by = user
        self.date_done = timezone.now()
        if form_data is not None:
            self.form_data = form_data
        self.save()
        logging.info("User %s resolved task %s", user, self.pk)

    def defer(self, date_deferred):
        """Defer the task to the given date"""
        self.date_deferred = date_deferred
        self.save()

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        # by default, only staff can manage requests
        # some tasks will override this to allow the foia owner to manage as well
        return user.is_staff


class OrphanTask(Task):
    """A communication that needs to be approved before showing it on the site"""

    type = "OrphanTask"
    reasons = (
        ("bs", "Bad Sender"),
        ("ib", "Incoming Blocked"),
        ("ia", "Invalid Address"),
    )
    reason = models.CharField(max_length=2, choices=reasons)
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    address = models.CharField(max_length=255)

    objects = OrphanTaskQuerySet.as_manager()
    template_name = "task/orphan.html"

    def __str__(self):
        return "Orphan Task"

    def display(self):
        """Display something useful and identifing"""
        return "{}: {}".format(self.get_reason_display(), self.address)

    def get_absolute_url(self):
        return reverse("orphan-task", kwargs={"pk": self.pk})

    def move(self, foia_pks, user):
        """Moves the comm and creates a ResponseTask for it"""
        moved_comms = self.communication.move(foia_pks, user)
        for moved_comm in moved_comms:
            ResponseTask.objects.create(
                communication=moved_comm, created_from_orphan=True
            )
            moved_comm.make_sender_primary_contact()

    def reject(self, blacklist=False):
        """If blacklist is true, should blacklist the sender's domain."""
        if blacklist:
            self.blacklist()

    def get_sender_domain(self):
        """Gets the domain of the sender's email address."""
        try:
            return self.communication.emails.all()[0].from_email.domain
        except (IndexError, AttributeError):
            return None

    def blacklist(self):
        """Adds the communication's sender's domain to the email blacklist."""
        domain = self.get_sender_domain()
        if domain is None:
            return
        try:
            blacklist, _ = BlacklistDomain.objects.get_or_create(domain=domain)
        except BlacklistDomain.MultipleObjectsReturned:
            blacklist = BlacklistDomain.objects.filter(domain=domain).first()
        blacklist.resolve_matches()


class PaymentInfoTask(Task):
    """Pull who to make the payment to"""

    type = "PaymentInfoTask"
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    amount = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)

    objects = PaymentInfoTaskQuerySet.as_manager()

    def __str__(self):
        return "Payment Info Task"

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        return self.communication.foia.has_perm(user, "tasks")


class SnailMailTask(Task):
    """A communication that needs to be snail mailed"""

    type = "SnailMailTask"
    category = models.CharField(max_length=1, choices=SNAIL_MAIL_CATEGORIES)
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    amount = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)
    switch = models.BooleanField(
        default=False,
        help_text="Designates we have switched to sending to this address "
        "from another form of communication due to some sort of error.  A "
        "note should be included in the communication with an explanation.",
    )
    reason = models.CharField(
        max_length=6,
        choices=(
            ("auto", "Automatic Lob sending was disabled"),
            ("addr", "FOIA had no address"),
            ("badadd", "Address field too long for Lob"),
            ("appeal", "This is an appeal"),
            ("pay", "This is a payment"),
            ("limit", "Over the payment limit"),
            ("pdf", "There was an error processing the PDF"),
            ("page", "The PDF was over the page limit"),
            ("attm", "There was an error processing an attachment"),
            ("lob", "There was an error sending via Lob"),
        ),
        help_text="Reason the snail mail task was created instead of "
        "auto sending via lob",
        blank=True,
    )
    error_msg = models.CharField(
        max_length=255, blank=True, help_text="The error message returned by lob"
    )

    objects = SnailMailTaskQuerySet.as_manager()

    def __str__(self):
        return "Snail Mail Task"

    def display(self):
        """Display something useful and identifing"""
        return "{}: {}".format(
            self.get_category_display(), self.communication.foia.title
        )

    def get_absolute_url(self):
        return reverse("snail-mail-task", kwargs={"pk": self.pk})

    def set_status(self, status):
        """Set the status of the comm and FOIA affiliated with this task"""
        comm = self.communication
        comm.status = status
        comm.save()
        comm.foia.status = status
        comm.foia.save(comment="snail mail task")
        comm.foia.update()

    def update_text(self, new_text):
        """Sets the body text of the communication"""
        comm = self.communication
        comm.communication = new_text
        comm.save()

    def record_check(self, number, user):
        """Records the check to a note on the request"""
        check = Check.objects.create(
            number=number,
            agency=self.communication.foia.agency,
            amount=self.amount,
            communication=self.communication,
            user=user,
        )
        check.send_email()

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        return self.communication.foia.has_perm(user, "tasks")


class ReviewAgencyTask(Task):
    """An agency has had one of its forms of communication have an error
    and new contact information is required"""

    type = "ReviewAgencyTask"
    sources = (
        ("staff", "Staff Review"),
        ("stale", "Stale Request"),
        ("email", "Bad Email"),
        ("fax", "Bad Fax"),
    )
    agency = models.ForeignKey("agency.Agency", on_delete=models.PROTECT)
    source = models.CharField(max_length=5, choices=sources, blank=True, null=True)

    objects = ReviewAgencyTaskQuerySet.as_manager()

    def __str__(self):
        return "Review Agency Task"

    def get_absolute_url(self):
        return reverse("review-agency-task", kwargs={"pk": self.pk})

    def get_review_data(self):
        """Get all the data on all open requests for the agency"""
        review_data = []

        def get_data(email_or_fax):
            """Helper function to get email or fax data"""
            if email_or_fax == "email":
                address_model = EmailAddress
                confirm_rel = "to_emails"
                error_fields = [
                    "email",
                    "datetime",
                    "recipient",
                    "code",
                    "error",
                    "event",
                    "reason",
                ]
            elif email_or_fax == "fax":
                address_model = PhoneNumber
                confirm_rel = "faxes"
                error_fields = [
                    "fax",
                    "datetime",
                    "recipient",
                    "error_type",
                    "error_code",
                    "error_id",
                ]

            open_requests = (
                self.agency.foiarequest_set.get_open()
                .order_by("%s__status" % email_or_fax, email_or_fax)
                .exclude(**{email_or_fax: None})
                .select_related(
                    "agency__jurisdiction", "composer", "email", "fax", "portal"
                )
                .annotate(
                    latest_response=ExtractDay(
                        Cast(
                            Now()
                            - Max(
                                Case(
                                    When(
                                        communications__response=True,
                                        then="communications__datetime",
                                    )
                                )
                            ),
                            models.DurationField(),
                        )
                    )
                )
                .only(
                    "pk",
                    "status",
                    "title",
                    "slug",
                    "agency__jurisdiction__slug",
                    "agency__jurisdiction__id",
                    "composer__datetime_submitted",
                    "date_estimate",
                    "portal__name",
                    "email__email",
                    "email__name",
                    "email__status",
                    "fax__number",
                    "fax__status",
                )
            )
            grouped_requests = [
                (k, list(v))
                for k, v in groupby(open_requests, lambda f: getattr(f, email_or_fax))
            ]
            # do seperate queries for per email addr/fax number stats
            # do annotations separately for performance reasons (limit joins)
            addresses = address_model.objects.annotate(
                error_count=Count("errors", distinct=True),
                last_error=Max("errors__datetime"),
            )
            addresses = addresses.in_bulk(g[0].pk for g in grouped_requests)
            addresses_confirm = address_model.objects.annotate(
                last_confirm=Max("%s__confirmed_datetime" % confirm_rel)
            )
            addresses_confirm = addresses_confirm.in_bulk(
                g[0].pk for g in grouped_requests
            )
            if email_or_fax == "email":
                addresses_open = address_model.objects.annotate(
                    last_open=Max("opens__datetime")
                )
                addresses_open = addresses_open.in_bulk(
                    g[0].pk for g in grouped_requests
                )

            review_data = []
            for addr, foias in grouped_requests:
                # fetch the address with the annotated stats
                addr = addresses[addr.pk]
                review_data.append(
                    {
                        "address": addr,
                        "error": addr.status == "error",
                        "errors": addr.errors.select_related(
                            "%s__communication__foia__agency__jurisdiction"
                            % email_or_fax
                        )
                        .order_by("-datetime")
                        .only(
                            *error_fields
                            + [
                                "%s__communication__foia__agency__jurisdiction__slug"
                                % email_or_fax,
                                "%s__communication__foia__slug" % email_or_fax,
                                "%s__communication__foia__title" % email_or_fax,
                            ]
                        )[:5],
                        "foias": foias,
                        "unacknowledged": any(f.status == "ack" for f in foias),
                        "total_errors": addr.error_count,
                        "last_error": addr.last_error,
                        "last_confirm": addresses_confirm[addr.pk].last_confirm,
                        "last_open": addresses_open[addr.pk].last_open
                        if email_or_fax == "email"
                        else None,
                        "checkbox_name": "foias-%d-%s-%d"
                        % (self.pk, email_or_fax, addr.pk),
                        "email_or_fax": email_or_fax,
                    }
                )
            return review_data

        review_data.extend(get_data("email"))
        review_data.extend(get_data("fax"))
        # snail mail
        foias = list(
            self.agency.foiarequest_set.get_open()
            .filter(email=None, fax=None)
            .select_related(
                "agency__jurisdiction", "composer", "email", "fax", "portal"
            )
            .annotate(
                latest_response=ExtractDay(
                    Cast(
                        Now()
                        - Max(
                            Case(
                                When(
                                    communications__response=True,
                                    then="communications__datetime",
                                )
                            )
                        ),
                        models.DurationField(),
                    )
                )
            )
            .only(
                "pk",
                "status",
                "title",
                "slug",
                "agency__jurisdiction__slug",
                "agency__jurisdiction__id",
                "composer__datetime_submitted",
                "date_estimate",
                "portal__name",
                "email__email",
                "email__name",
                "email__status",
                "fax__number",
                "fax__status",
            )
        )
        if foias:
            review_data.append(
                {
                    "address": "Snail Mail",
                    "foias": foias,
                    "checkbox_name": "%d-snail" % self.pk,
                    "unacknowledged": any(f.status == "ack" for f in foias),
                }
            )

        return review_data

    def update_contact(self, email_or_fax, foia_list, update_info, snail):
        """Updates the contact info on the agency and the provided requests."""
        # pylint: disable=too-many-branches, import-outside-toplevel
        from muckrock.agency.models import AgencyEmail, AgencyPhone

        is_email = isinstance(email_or_fax, EmailAddress) and not snail
        is_fax = isinstance(email_or_fax, PhoneNumber) and not snail

        if update_info:
            # clear primary emails if we are updating with any new info
            agency_emails = self.agency.agencyemail_set.filter(
                request_type="primary", email_type="to"
            )
            for agency_email in agency_emails:
                agency_email.request_type = "none"
                agency_email.email_type = "none"
                agency_email.save()

            # clear primary faxes if updating with a fax or snail mail address
            if is_fax or snail:
                agency_faxes = self.agency.agencyphone_set.filter(
                    request_type="primary", phone__type="fax"
                )
                for agency_fax in agency_faxes:
                    agency_fax.request_type = "none"
                    agency_fax.save()

        if is_email:
            if update_info:
                AgencyEmail.objects.create(
                    email=email_or_fax,
                    agency=self.agency,
                    request_type="primary",
                    email_type="to",
                )
            for foia in foia_list:
                foia.email = email_or_fax
                if foia.fax and foia.fax.status != "good":
                    foia.fax = None
                foia.save()

        elif is_fax:
            if update_info:
                AgencyPhone.objects.create(
                    phone=email_or_fax, agency=self.agency, request_type="primary"
                )
            for foia in foia_list:
                foia.email = None
                foia.fax = email_or_fax
                foia.save()

        elif snail:
            for foia in foia_list:
                foia.email = None
                foia.fax = None
                foia.address = self.agency.get_addresses().first()
                foia.save()

    def latest_response(self):
        """Returns the latest response from the agency"""
        # pylint: disable=import-outside-toplevel
        from muckrock.foia.models import FOIACommunication

        latest_communication = (
            FOIACommunication.objects.filter(foia__agency=self.agency)
            .order_by("-datetime")
            .first()
        )
        if latest_communication:
            return latest_communication.datetime
        else:
            return None


class FlaggedTask(Task):
    """A user has flagged a request, agency or jurisdiction"""

    type = "FlaggedTask"
    text = models.TextField()
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    # Allow FOIA to be set null, in the case that they add custom contact information,
    # which creates a flag task, and they try to edit the request before it is sent,
    # which will delete the request and return you to the composer
    foia = models.ForeignKey(
        "foia.FOIARequest", blank=True, null=True, on_delete=models.SET_NULL
    )
    agency = models.ForeignKey(
        "agency.Agency", blank=True, null=True, on_delete=models.PROTECT
    )
    jurisdiction = models.ForeignKey(
        Jurisdiction, blank=True, null=True, on_delete=models.PROTECT
    )
    category = models.TextField(choices=FLAG_CATEGORIES, blank=True)

    objects = FlaggedTaskQuerySet.as_manager()

    def __str__(self):
        return "Flagged Task"

    def display(self):
        """Display something useful and identifing"""
        if self.foia:
            return self.foia.title
        elif self.agency:
            return self.agency.name
        elif self.jurisdiction:
            return self.jurisdiction.name
        else:
            return "None"

    def get_absolute_url(self):
        return reverse("flagged-task", kwargs={"pk": self.pk})

    def flagged_object(self):
        """Return the object that was flagged (should only ever be one, and never none)"""
        if self.foia:
            return self.foia
        elif self.agency:
            return self.agency
        elif self.jurisdiction:
            return self.jurisdiction
        else:
            raise AttributeError("No flagged object.")

    def reply(self, text):
        """Send an email reply to the user that raised the flag."""
        support.delay(self.user.pk, text, self.pk)

    def create_zoho_ticket(self):
        """Create a Zoho ticket"""

        def make_url(obj):
            """Make a URL"""
            if obj is None:
                return ""
            else:
                return '<p><a href="{}{}" target="_blank">{}</a></p>'.format(
                    settings.MUCKROCK_URL, obj.get_absolute_url(), obj
                )

        contact_id = self.get_contact_id(self.user)
        if contact_id is None:
            return None
        description = bleach.clean(self.text)
        subject = description[:50] or "-No Subject-"
        description = linebreaks(urlize(description))

        description += make_url(self.foia)
        description += make_url(self.agency)
        description += make_url(self.jurisdiction)

        email = (
            self.user.email
            if self.user and self.user.email
            else settings.DEFAULT_FROM_EMAIL
        )

        response = zoho_post(
            "tickets",
            json={
                "subject": subject,
                "departmentId": settings.ZOHO_DEPT_IDS["muckrock"],
                "contactId": contact_id,
                "email": email,
                "description": description,
                "channel": "Web",
                "category": "Flag",
                "subCategory": self.get_category_display(),
            },
        )
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()["id"]
        else:
            return None

    def get_contact_id(self, user):
        """Get a zoho contact id for the contact with the given email address"""
        if user is None or not user.email:
            user = User.objects.get(username="MuckrockStaff")
        response = zoho_get("contacts/search", params={"limit": 1, "email": user.email})
        response.raise_for_status()
        if response.status_code == 200:
            contacts = response.json()
            if contacts["count"] > 0:
                return contacts["data"][0]["id"]

        # if we could not find an existing contact, we will create one
        response = zoho_post(
            "contacts",
            json={
                "lastName": user.profile.full_name
                or "Anonymous",  # lastName is required
                "email": user.email,
                "customFields": {"username": user.username},
            },
        )
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()["id"]
        else:
            return None

    def create_zendesk_ticket(self):
        # pylint: disable=too-many-branches
        client = Zenpy(
            email=settings.ZENDESK_EMAIL,
            subdomain=settings.ZENDESK_SUBDOMAIN,
            token=settings.ZENDESK_TOKEN,
        )

        description = self.text
        tag = self.category.replace(" ", "_")
        # automatically extend no response tags with the acknowledgment
        # status of the foia request
        if tag == "no_response" and self.foia:
            if self.foia.has_ack():
                tag += "_ack"
            else:
                tag += "_no_ack"
        tags = ["flag", tag]

        for obj_name in ["foia", "agency", "jurisdiction"]:
            obj = getattr(self, obj_name)
            if obj:
                description += "\n{}{}".format(
                    settings.MUCKROCK_URL, obj.get_absolute_url()
                )
                tags.append("{}_flag".format(obj_name))

        if self.foia:
            description += (
                "\nNOTE: If the FOIA does not exist, "
                "the user may have deleted it, and you may safely close this ticket."
            )

        if self.user:
            entitlements = list(
                self.user.organizations.values_list(
                    "entitlement__slug", flat=True
                ).distinct()
            )
            if "free" in entitlements and len(entitlements) > 1:
                entitlements.remove("free")
            tags.extend(entitlements)

        ticket_data = {
            "subject": self.get_category_display() or "Generic Flag",
            "comment": Comment(body=description),
            "type": "task",
            "priority": "normal",
            "status": "new",
            "tags": tags,
        }
        if self.foia:
            ticket_data["custom_fields"] = [
                {"id": MR_NUMBER_FIELD, "value": self.foia.pk}
            ]
        if self.user:
            user_data = {
                "name": self.user.profile.full_name or self.user.username,
                "external_id": str(self.user.profile.uuid),
            }
            if self.user.email:
                user_data["email"] = self.user.email
            org_data = {
                "name": self.user.profile.organization.name,
                "external_id": str(self.user.profile.organization.uuid),
            }
        else:
            user_data = {"name": "Anonymous User"}
            org_data = {}

        if org_data:
            org = client.organizations.create_or_update(ZenOrganization(**org_data))
            user_data["organization_id"] = org.id
            ticket_data["organization_id"] = org.id
        user = client.users.create_or_update(ZenUser(**user_data))
        ticket_data["requester_id"] = user.id
        ticket_audit = client.tickets.create(Ticket(**ticket_data))
        return ticket_audit.ticket.id

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        if self.foia:
            return self.foia.has_perm(user, "tasks")
        else:
            return super().check_permission(user)


class ProjectReviewTask(Task):
    """Created when a project is published and needs approval."""

    type = "ProjectReviewTask"
    project = models.ForeignKey("project.Project", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    objects = ProjectReviewTaskQuerySet.as_manager()

    def __str__(self):
        return "Project Review Task"

    def get_absolute_url(self):
        return reverse("projectreview-task", kwargs={"pk": self.pk})

    def reply(self, text, action="reply"):
        """Send an email reply to the user that raised the flag."""
        send_to = [contributor.email for contributor in self.project.contributors.all()]
        project_email = TemplateEmail(
            to=send_to,
            extra_context={"action": action, "message": text, "task": self},
            subject="%s %s" % (self.project, action),
            text_template="message/project/%s.txt" % action,
            html_template="message/project/%s.html" % action,
        )
        project_email.send(fail_silently=False)
        return project_email

    def approve(self, text):
        """Mark the project approved and notify the user."""
        self.project.approved = True
        self.project.date_approved = date.today()
        self.project.save()
        return self.reply(text, "approved")

    def reject(self, text):
        """Mark the project private and notify the user."""
        self.project.private = True
        self.project.save()
        return self.reply(text, "rejected")


class NewAgencyTask(Task):
    """A new agency has been created and needs approval"""

    type = "NewAgencyTask"
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    agency = models.ForeignKey("agency.Agency", on_delete=models.CASCADE)

    objects = NewAgencyTaskQuerySet.as_manager()

    def __str__(self):
        return "New Agency Task"

    def display(self):
        """Display something useful and identifing"""
        return self.agency.name

    def get_absolute_url(self):
        return reverse("new-agency-task", kwargs={"pk": self.pk})

    def approve(self):
        """Approves agency, resends pending requests to it"""
        self._resolve_agency()

    def reject(self, replacement_agency=None):
        """Reject agency, resend to replacement if one is specified"""
        if replacement_agency is not None:
            self._resolve_agency(replacement_agency)
        else:
            self.agency.status = "rejected"
            self.agency.save()
            foias = self.agency.foiarequest_set.select_related("composer").annotate(
                count=Count("composer__foias")
            )
            if foias:
                # only send an email if they submitted a request with it
                subject = 'We need your help with your request, "{}"'.format(
                    foias[0].title
                )
                if len(foias) > 1:
                    subject += ", and others"
                TemplateEmail(
                    subject=subject,
                    user=self.user,
                    text_template="task/email/agency_rejected.txt",
                    html_template="task/email/agency_rejected.html",
                    extra_context={
                        "agency": self.agency,
                        "foias": foias,
                        "url": settings.MUCKROCK_URL,
                    },
                ).send(fail_silently=False)
            for foia in foias:
                foia.composer.return_requests(1)
                foia.delete()
            for composer in self.agency.composers.all():
                composer.agencies.remove(self.agency)
                if composer.foias.count() == 0:
                    if composer.revokable():
                        composer.revoke()
                    composer.status = "started"
                    composer.save()

    def _resolve_agency(self, replacement_agency=None):
        """Approves or rejects an agency and re-submits the pending requests"""
        if replacement_agency:
            self.agency.status = "rejected"
            proxy_info = replacement_agency.get_proxy_info()
        else:
            self.agency.status = "approved"
            proxy_info = self.agency.get_proxy_info()
        self.agency.save()
        for foia in self.agency.foiarequest_set.all():
            # first switch foia to use replacement agency
            if replacement_agency:
                foia.agency = replacement_agency
                foia.save(comment="new agency task")
            if foia.communications.exists():
                # regenerate communication text in case jurisdiction changed
                comm = foia.communications.first()
                comm.communication = FOIATemplate.objects.render(
                    [foia.agency],
                    foia.user,
                    foia.composer.requested_docs,
                    edited_boilerplate=foia.composer.edited_boilerplate,
                    proxy=proxy_info.get("from_user"),
                )
                comm.save()
                foia.submit(clear=True)

    def spam(self, user):
        """Reject the agency and block the user"""
        self.agency.status = "rejected"
        self.agency.save()
        if self.user.is_authenticated:
            self.user.is_active = False
            self.user.save()
        self.agency.foiarequest_set.all().delete()

        send_mail(
            subject="%s blocked as spammer" % self.user.username,
            message=render_to_string(
                "text/task/spam.txt",
                {
                    "url": settings.MUCKROCK_URL + self.get_absolute_url(),
                    "spammer": self.user.username,
                    "moderator": user.username,
                    "agency": self.agency.name,
                },
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )


class ResponseTask(Task):
    """A response has been received and needs its status set"""

    type = "ResponseTask"
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    created_from_orphan = models.BooleanField(default=False)
    # for predicting statuses
    predicted_status = models.CharField(
        max_length=10, choices=STATUS, blank=True, null=True
    )
    status_probability = models.IntegerField(blank=True, null=True)
    scan = models.BooleanField(default=False)

    objects = ResponseTaskQuerySet.as_manager()

    def __str__(self):
        return "Response Task"

    def get_absolute_url(self):
        return reverse("response-task", kwargs={"pk": self.pk})

    def set_status(self, status):
        """Forward to form logic, for use in classify_status task"""
        # pylint: disable=import-outside-toplevel
        from muckrock.task.forms import ResponseTaskForm

        form = ResponseTaskForm(task=self)
        form.set_status(status, set_foia=True, comms=[self.communication])

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        return self.communication.foia.has_perm(user, "tasks")


class StatusChangeTask(Task):
    """A user has changed the status on a request"""

    type = "StatusChangeTask"
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    old_status = models.CharField(max_length=255)
    foia = models.ForeignKey("foia.FOIARequest", on_delete=models.PROTECT)

    objects = StatusChangeTaskQuerySet.as_manager()

    def __str__(self):
        return "Status Change Task"

    def get_absolute_url(self):
        return reverse("status-change-task", kwargs={"pk": self.pk})

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        return self.foia.has_perm(user, "tasks")


class CrowdfundTask(Task):
    """Created when a crowdfund is finished"""

    type = "CrowdfundTask"
    crowdfund = models.ForeignKey("crowdfund.Crowdfund", on_delete=models.PROTECT)

    objects = CrowdfundTaskQuerySet.as_manager()

    def __str__(self):
        return "Crowdfund Task"

    def get_absolute_url(self):
        return reverse("crowdfund-task", kwargs={"pk": self.pk})


class MultiRequestTask(Task):
    """Created when a composer with multiple agencies is created and needs
    approval.
    """

    type = "MultiRequestTask"
    composer = models.ForeignKey("foia.FOIAComposer", on_delete=models.PROTECT)

    objects = MultiRequestTaskQuerySet.as_manager()

    def __str__(self):
        return "Multi-Request Task"

    def get_absolute_url(self):
        return reverse("multirequest-task", kwargs={"pk": self.pk})

    def submit(self, agency_list):
        """Submit the composer"""
        # pylint: disable=not-callable, import-outside-toplevel
        from muckrock.foia.tasks import composer_delayed_submit

        return_requests = 0
        with transaction.atomic():
            for agency in self.composer.agencies.all():
                if str(agency.pk) not in agency_list:
                    self.composer.agencies.remove(agency)
                    self.composer.foias.filter(agency=agency).delete()
                    return_requests += 1
            self.composer.return_requests(return_requests)
            transaction.on_commit(
                lambda: composer_delayed_submit.apply_async(
                    args=(self.composer.pk, True, None)
                )
            )

    def reject(self):
        """Reject the composer and return the user their requests"""
        self.composer.return_requests()
        self.composer.status = "started"
        self.composer.save()


class PortalTask(Task):
    """An admin needs to interact with a portal"""

    type = "PortalTask"
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    category = models.CharField(max_length=1, choices=PORTAL_CATEGORIES)
    reason = models.TextField(blank=True)

    objects = PortalTaskQuerySet.as_manager()

    def __str__(self):
        return "Portal Task"

    def display(self):
        """Display something useful and identifing"""
        return self.communication.foia.title

    def get_absolute_url(self):
        return reverse("portal-task", kwargs={"pk": self.pk})

    def set_status(self, status):
        """Set the status of the comm and FOIA affiliated with this task"""
        comm = self.communication
        comm.status = status
        comm.save()
        comm.foia.status = status
        comm.foia.save(comment="portal task")
        comm.foia.update()

    def check_permission(self, user):
        """Check if a user has permission to manage this task"""
        return self.communication.foia.has_perm(user, "tasks")


class NewPortalTask(Task):
    """A portal has been detected where we do not have one in the system"""

    type = "NewPortalTask"
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    portal_type = models.CharField(choices=PORTAL_TYPES, max_length=11)

    objects = NewPortalTaskQuerySet.as_manager()

    def __str__(self):
        return "New Portal Task"

    def display(self):
        """Display something useful and identifing"""
        return self.communication.foia.title

    def get_absolute_url(self):
        return reverse("new-portal-task", kwargs={"pk": self.pk})


# Retired Tasks


class GenericTask(Task):
    """A generic task"""

    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return "Generic Task"


class FailedFaxTask(Task):
    """
    Deprecated: keeping this model around to not lose historical data
    A fax for this communication failed"""

    type = "FailedFaxTask"
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.PROTECT
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return "Failed Fax Task"

    def get_absolute_url(self):
        return reverse("failed-fax-task", kwargs={"pk": self.pk})


class RejectedEmailTask(Task):
    """
    Deprecated: Keeping this model around to not lose historical data

    A FOIA request has had an outgoing email rejected"""

    type = "RejectedEmailTask"
    categories = (("b", "Bounced"), ("d", "Dropped"))
    category = models.CharField(max_length=1, choices=categories)
    foia = models.ForeignKey(
        "foia.FOIARequest", blank=True, null=True, on_delete=models.PROTECT
    )
    email = models.EmailField(blank=True)
    error = models.TextField(blank=True)
    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return "Rejected Email Task"

    def get_absolute_url(self):
        return reverse("rejected-email-task", kwargs={"pk": self.pk})


class StaleAgencyTask(Task):
    """Deprecated: Replaced by review agency task

    An agency has gone stale"""

    type = "StaleAgencyTask"
    agency = models.ForeignKey("agency.Agency", on_delete=models.PROTECT)

    objects = models.Manager()

    def __str__(self):
        return "Stale Agency Task"

    def get_absolute_url(self):
        return reverse("stale-agency-task", kwargs={"pk": self.pk})


class NewExemptionTask(Task):
    """
    Depracted: folded into flag tasks

    Created when a new exemption is submitted for our review."""

    type = "NewExemptionTask"
    foia = models.ForeignKey("foia.FOIARequest", on_delete=models.PROTECT)
    language = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    objects = models.Manager()

    def __str__(self):
        return "New Exemption Task"

    def display(self):
        """Display something useful and identifing"""
        return self.foia.title

    def get_absolute_url(self):
        return reverse("newexemption-task", kwargs={"pk": self.pk})


# Not a task, but used by tasks
class BlacklistDomain(models.Model):
    """A domain to be blacklisted from sending us emails"""

    domain = models.CharField(max_length=255)

    def __str__(self):
        return self.domain

    def resolve_matches(self):
        """Resolves any orphan tasks that match this blacklisted domain."""
        tasks_to_resolve = OrphanTask.objects.get_from_domain(self.domain)
        for task in tasks_to_resolve:
            task.resolve()


class FileDownloadLink(models.Model):
    """A URL to look for in communications which needs to be downloaded"""

    name = models.CharField(max_length=255, help_text="The name of the download site")
    url = models.CharField(
        max_length=255,
        help_text="The URL to look for in the communication text. "
        "You may use * to match anything: 'https://*.sharefile.com'",
    )

    def __str__(self):
        return self.name
