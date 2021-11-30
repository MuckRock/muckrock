"""
Models for the organization application
"""

# Django
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.expressions import F
from django.db.models.functions import Greatest
from django.urls import reverse

# Standard Library
import logging
from uuid import uuid4

# Third Party
import stripe

# MuckRock
from muckrock.core.utils import squarelet_post
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.organization.querysets import OrganizationQuerySet

logger = logging.getLogger(__name__)
stripe.api_version = "2015-10-16"


class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""

    # pylint: disable=too-many-instance-attributes

    objects = OrganizationQuerySet.as_manager()

    uuid = models.UUIDField(
        "UUID", unique=True, editable=False, default=uuid4, db_index=True
    )

    users = models.ManyToManyField(
        User, through="organization.Membership", related_name="organizations"
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    private = models.BooleanField(default=False)
    individual = models.BooleanField(default=True)
    entitlement = models.ForeignKey(
        "organization.Entitlement", on_delete=models.PROTECT, null=True
    )
    card = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(max_length=255, blank=True)

    requests_per_month = models.IntegerField(
        default=0,
        help_text="How many monthly requests this organization gets each month",
    )
    monthly_requests = models.IntegerField(
        default=0,
        help_text="How many recurring monthly requests are left for this month - these do "
        "not roll over and are just reset to `requests_per_month` on `date_update`",
    )
    number_requests = models.IntegerField(
        default=0,
        help_text="How many individually purchased requests this organization has - "
        "these never expire and are unaffected by the monthly roll over",
    )
    date_update = models.DateField(null=True)

    payment_failed = models.BooleanField(default=False)

    def __str__(self):
        if self.individual:
            return "{} (Individual)".format(self.name)
        else:
            return self.name

    @property
    def display_name(self):
        """Display 'Personal Account' for individual organizations"""
        if self.individual:
            return "Personal Account"
        else:
            return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse("org-detail", kwargs={"slug": self.slug})

    def has_member(self, user):
        """Is the user a member of this organization?"""
        return self.users.filter(pk=user.pk).exists()

    def has_admin(self, user):
        """Is the user an admin of this organization?"""
        return self.users.filter(pk=user.pk, memberships__admin=True).exists()

    def update_data(self, data):
        """Set updated data from squarelet"""

        logger.info("update data org %s %s", self.pk, data)

        if len(data["entitlements"]) > 1:
            logger.warning(
                "Organization %s has multiple entitlements: %s",
                self.pk,
                ", ".join(e["slug"] for e in data["entitlements"]),
            )
        if data["entitlements"]:
            entitlement_data = max(
                data["entitlements"],
                key=lambda e: e["resources"].get("base_requests", 0),
            )
            self.entitlement, _created = Entitlement.objects.update_or_create(
                slug=entitlement_data["slug"],
                defaults={
                    "name": entitlement_data["name"],
                    "description": entitlement_data["description"],
                    "resources": entitlement_data["resources"],
                },
            )
            date_update = entitlement_data["date_update"]
        else:
            self.entitlement, _created = Entitlement.objects.get_or_create(
                slug="free", defaults={"name": "Free"}
            )
            date_update = None

        # calc reqs/month in case it has changed
        self.requests_per_month = self.entitlement.requests_per_month(data["max_users"])

        # if date update has changed, then this is a monthly restore of the
        # subscription, and we should restore monthly requests.  If not, requests
        # per month may have changed if they changed their plan or their user count,
        # in which case we should add the difference to their monthly requests
        # if requests per month increased
        if self.date_update == date_update:
            # add additional monthly requests immediately
            self.monthly_requests = F("monthly_requests") + Greatest(
                self.requests_per_month - F("requests_per_month"), 0
            )
        else:
            # reset monthly requests when date_update is updated
            self.monthly_requests = self.requests_per_month
            self.date_update = date_update

        # update the remaining fields
        fields = [
            "name",
            "slug",
            "individual",
            "private",
            "card",
            "payment_failed",
            "avatar_url",
        ]
        for field in fields:
            if field in data:
                setattr(self, field, data[field])
        self.save()

    @transaction.atomic
    def make_requests(self, amount):
        """Try to deduct requests from the organization's balance"""
        request_count = {"monthly": 0, "regular": 0}
        organization = Organization.objects.select_for_update().get(pk=self.pk)

        request_count["monthly"] = min(amount, organization.monthly_requests)
        amount -= request_count["monthly"]

        request_count["regular"] = min(amount, organization.number_requests)
        amount -= request_count["regular"]

        if amount > 0:
            raise InsufficientRequestsError(amount)

        organization.monthly_requests -= request_count["monthly"]
        organization.number_requests -= request_count["regular"]
        organization.save()
        return request_count

    def return_requests(self, amounts):
        """Return requests to the organization's balance"""
        self.monthly_requests = F("monthly_requests") + amounts["monthly"]
        self.number_requests = F("number_requests") + amounts["regular"]
        self.save()

    def add_requests(self, amount):
        """Add requests"""
        self.number_requests = F("number_requests") + amount
        self.save()

    def pay(self, amount, description, token, save_card, fee_amount=0):
        """Pay via Squarelet API"""
        # pylint: disable=too-many-arguments
        resp = squarelet_post(
            "/api/charges/",
            data={
                "organization": self.uuid,
                "amount": amount,
                "fee_amount": fee_amount,
                "description": description,
                "token": token,
                "save_card": save_card,
            },
        )
        logger.info("Squarelet response: %s %s", resp.status_code, resp.content)
        resp.raise_for_status()
        resp_json = resp.json()
        if "card" in resp_json:
            self.card = resp_json["card"]
            self.save()


class Membership(models.Model):
    """Through table for organization membership"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    active = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return "{} in {}".format(self.user, self.organization)


# remove, convert to entitlement
class Plan(models.Model):
    """Plans that organizations can subscribe to"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    minimum_users = models.PositiveSmallIntegerField(default=1)
    base_requests = models.PositiveSmallIntegerField(default=0)
    requests_per_user = models.PositiveSmallIntegerField(default=0)
    feature_level = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

    def requests_per_month(self, users):
        """Calculate how many requests an organization gets per month on this plan
        for a given number of users"""
        return (
            self.base_requests + (users - self.minimum_users) * self.requests_per_user
        )


class Entitlement(models.Model):
    """Entitlements represent features and resources an organization has paid for"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()

    resources = models.JSONField(default=dict)
    resource_fields = {
        "minimum_users": 1,
        "feature_level": 0,
        "base_requests": 0,
        "requests_per_user": 0,
    }

    def __str__(self):
        return self.name

    def requests_per_month(self, users):
        """Calculate how many requests an organization gets per month on this
        entitlement for a given number of users"""
        return (
            self.base_requests + (users - self.minimum_users) * self.requests_per_user
        )


# dynamically create properties for all defined resource fields
for field_, default in Entitlement.resource_fields.items():
    setattr(
        Entitlement,
        field_,
        property(lambda self, f=field_, d=default: self.resources.get(f, d)),
    )
