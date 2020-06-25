"""
Agency Model
"""

# Django
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import F, Value
from django.db.models.functions import Concat
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

# Standard Library
import logging

# Third Party
from easy_thumbnails.fields import ThumbnailerImageField

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core.utils import squarelet_post
from muckrock.jurisdiction.models import Jurisdiction, RequestHelper
from muckrock.task.models import NewAgencyTask

logger = logging.getLogger(__name__)


class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class AgencyQuerySet(models.QuerySet):
    """Object manager for Agencies"""

    # pylint: disable=too-many-public-methods

    def get_approved(self):
        """Get all approved agencies"""
        return self.filter(status="approved")

    def get_approved_and_pending(self, user):
        """Get approved and given user's pending agencies"""
        if user.is_authenticated:
            return self.filter(Q(status="approved") | Q(status="pending", user=user))
        else:
            return self.get_approved()

    def get_siblings(self, agency):
        """Get all approved agencies in the same jurisdiction as the given agency."""
        return (
            self.filter(jurisdiction=agency.jurisdiction)
            .exclude(id=agency.id)
            .filter(status="approved")
            .order_by("name")
        )

    def create_new(self, name, jurisdiction, user):
        """Create a pending agency with a NewAgency task"""
        user = user if user.is_authenticated else None
        name = name.strip()

        existing_agency = self.filter(
            name=name, jurisdiction=jurisdiction, user=user, status="pending"
        ).first()
        if existing_agency:
            return existing_agency

        agency = self.create(
            name=name,
            slug=(slugify(name) or "untitled"),
            jurisdiction=jurisdiction,
            user=user,
            status="pending",
        )
        NewAgencyTask.objects.create(user=user, agency=agency)
        return agency


class Agency(models.Model, RequestHelper):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=255)
    mail_name = models.CharField(max_length=40)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(
        Jurisdiction, related_name="agencies", on_delete=models.PROTECT
    )
    types = models.ManyToManyField(AgencyType, blank=True)
    status = models.CharField(
        choices=(
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ),
        max_length=8,
        default="pending",
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        help_text="The user who submitted this agency",
        on_delete=models.PROTECT,
    )
    appeal_agency = models.ForeignKey(
        "self",
        related_name="appeal_for",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    image = ThumbnailerImageField(
        upload_to="agency_images",
        blank=True,
        null=True,
        resize_source={"size": (900, 600), "crop": "smart"},
    )
    image_attr_line = models.CharField(
        blank=True, max_length=255, help_text="May use html"
    )
    public_notes = models.TextField(blank=True, help_text="May use html")

    addresses = models.ManyToManyField(
        "communication.Address", through="AgencyAddress", related_name="agencies"
    )
    emails = models.ManyToManyField(
        "communication.EmailAddress", through="AgencyEmail", related_name="agencies"
    )
    phones = models.ManyToManyField(
        "communication.PhoneNumber", through="AgencyPhone", related_name="agencies"
    )
    portal = models.ForeignKey(
        "portal.Portal",
        related_name="agencies",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)

    form = models.ForeignKey(
        "AgencyRequestForm",
        blank=True,
        null=True,
        related_name="agencies",
        on_delete=models.SET_NULL,
    )

    url = models.URLField(
        blank=True, verbose_name="FOIA Web Page", help_text="Begin with http://"
    )
    notes = models.TextField(blank=True)
    aliases = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    website = models.CharField(max_length=255, blank=True)
    twitter = models.CharField(max_length=255, blank=True)
    twitter_handles = models.TextField(blank=True)
    foia_logs = models.URLField(
        blank=True, verbose_name="FOIA Logs", help_text="Begin with http://"
    )
    foia_guide = models.URLField(
        blank=True, verbose_name="FOIA Processing Guide", help_text="Begin with http://"
    )
    exempt = models.BooleanField(
        default=False,
        help_text="Mark agencies as exempt from public record laws.  Use the exempt note "
        "for further explanation",
    )
    uncooperative = models.BooleanField(
        default=False,
        verbose_name="Scowfflaw",
        help_text="Mark agencies as unwilling to process our requests.  Use the exempt "
        "note for further explanation",
    )
    exempt_note = models.CharField(max_length=255, blank=True)
    requires_proxy = models.BooleanField(default=False)

    objects = AgencyQuerySet.as_manager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            "agency-detail",
            kwargs={
                "jurisdiction": self.jurisdiction.slug,
                "jidx": self.jurisdiction.pk,
                "slug": self.slug,
                "idx": self.pk,
            },
        )

    def save(self, *args, **kwargs):
        """Save the agency"""
        # pylint: disable=signature-differs
        self.slug = slugify(self.slug)
        self.name = self.name.strip()
        super(Agency, self).save(*args, **kwargs)

    def link_display(self):
        """Returns link if approved"""
        if self.status == "approved":
            return mark_safe(
                '<a href="%s">%s</a>' % (self.get_absolute_url(), self.name)
            )
        else:
            return self.name

    def count_thanks(self):
        """Count how many thanks this agency has received"""
        return (
            self.foiarequest_set.filter(communications__thanks=True).distinct().count()
        )

    def get_requests(self):
        """Just returns the foiareqest_set value. Used for compatability with RequestHeper mixin"""
        return self.foiarequest_set

    def get_user(self):
        """Get the agency user for this agency"""
        try:
            return self.profile.user
        except Profile.DoesNotExist:
            data = {
                "name": self.name,
                "preferred_username": self.name,
                "is_agency": True,
            }
            # error handling?
            resp = squarelet_post("/api/users/", data=data)
            user_json = resp.json()
            user_json["agency"] = self
            user, _ = Profile.objects.squarelet_update_or_create(
                user_json["uuid"], user_json
            )
            return user

    def get_emails(self, request_type="primary", email_type="to"):
        """Get the specified type of email addresses for this agency"""
        return self.emails.filter(
            status="good",
            agencyemail__request_type=request_type,
            agencyemail__email_type=email_type,
        )

    def get_faxes(self, request_type="primary"):
        """Get the contact fax numbers"""
        return self.phones.filter(
            type="fax", status="good", agencyphone__request_type=request_type
        )

    def get_phones(self, request_type="none"):
        """Get the phone numbers"""
        return self.phones.filter(type="phone", agencyphone__request_type=request_type)

    def get_addresses(self, request_type="primary"):
        """Get the contact addresses"""
        return self.addresses.filter(agencyaddress__request_type=request_type)

    def get_proxy_info(self):
        """Handle proxy users for request creation in this agency"""
        if self.requires_proxy or self.jurisdiction.legal.always_proxy:
            proxy_user = self.jurisdiction.get_proxy()
            if proxy_user is None:
                return {
                    "proxy": True,
                    "missing_proxy": True,
                    "warning": "This agency and jurisdiction requires requestors to be "
                    "in-state citizens.  We do not currently have a citizen proxy "
                    "requestor on file for this state, so we will file this request "
                    "in your name.",
                }
            else:
                return {
                    "from_user": proxy_user,
                    "proxy": True,
                    "missing_proxy": False,
                    "warning": "This agency and jurisdiction requires requestors to be "
                    "in-state citizens.  This request will be filed in the name "
                    "of one of our volunteer filers for this state.",
                }
        else:
            return {"proxy": False, "missing_proxy": False}

    def has_open_review_task(self):
        """Is there an open review agency task for this agency"""
        return self.reviewagencytask_set.filter(resolved=False).exists()

    @property
    def email(self):
        """The main email"""
        return self.get_emails("primary", "to").first()

    @property
    def other_emails(self):
        """The cc emails"""
        return self.get_emails("primary", "cc")

    @property
    def fax(self):
        """The primary fax"""
        return self.get_faxes("primary").first()

    @property
    def address(self):
        """The primary address"""
        return self.get_addresses("primary").first()

    @transaction.atomic
    def merge(self, agency, user):
        """Merge the other agency into this agency"""
        replace_relations = [
            "foiarequest_set",
            "foiamachinerequest_set",
            "reviewagencytask_set",
            "flaggedtask_set",
            "newagencytask_set",
            "staleagencytask_set",
        ]
        for relation in replace_relations:
            getattr(agency, relation).update(agency=self)

        replace_self_relations = [
            ("appeal_agency", "appeal_for"),
            ("parent", "children"),
        ]
        for forward, backward in replace_self_relations:
            getattr(agency, backward).update(**{forward: self})

        replace_m2m = ["composers", "multirequests", "types", "foiasavedsearch_set"]
        for relation in replace_m2m:
            getattr(self, relation).add(*getattr(agency, relation).all())
            getattr(agency, relation).clear()

        # move emails/phone numbers/addresses over,
        # with types set to 'none', if doesn't already exist
        # on new agency (with any types)
        agency.agencyemail_set.exclude(email__in=self.emails.all()).update(
            request_type="none", email_type="none", agency=self
        )
        agency.agencyphone_set.exclude(phone__in=self.phones.all()).update(
            request_type="none", agency=self
        )
        agency.agencyaddress_set.exclude(address__in=self.addresses.all()).update(
            request_type="none", agency=self
        )

        # just update user on comms
        # we don't want to create a user for the bad agency if one doesn't exist
        try:
            old_user = agency.profile.user
            new_user = self.get_user()
            old_user.sent_communications.update(from_user=new_user)
            old_user.received_communications.update(to_user=new_user)
        except Profile.DoesNotExist:
            pass

        # mark the old agency as rejected and leave a note that it was merged
        agency.status = "rejected"
        agency.notes = Concat(
            F("notes"),
            Value(
                "\n\nThis agency was merged into agency "
                '"{}" (#{}) by {} on {}'.format(
                    self.name, self.pk, user.username, timezone.now()
                )
            ),
        )
        agency.save()

        self.notes = Concat(
            F("notes"),
            Value(
                '\n\nAgency "{}" (#{}) was merged into this agency '
                "by {} on {}".format(
                    agency.name, agency.pk, user.username, timezone.now()
                )
            ),
        )
        self.save()

    class Meta:
        verbose_name_plural = "agencies"
        permissions = (
            ("view_emails", "Can view private contact information"),
            ("merge_agency", "Can merge two agencies together"),
            ("mass_import", "Can mass import a CSV of agencies"),
        )
