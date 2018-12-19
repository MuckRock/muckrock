"""
Models for the organization application
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models.expressions import F
from django.utils.text import slugify

# Standard Library
import logging
from uuid import uuid4

# Third Party
import stripe

# MuckRock
from muckrock.core.exceptions import SquareletError
from muckrock.core.utils import squarelet_post
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.organization.choices import Plan
from muckrock.organization.querysets import OrganizationQuerySet

logger = logging.getLogger(__name__)
stripe.api_version = '2015-10-16'


class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""
    # pylint: disable=too-many-instance-attributes

    objects = OrganizationQuerySet.as_manager()

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    users = models.ManyToManyField(
        User, through="organization.Membership", related_name='organizations'
    )

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, blank=True)  # XXX no blank
    private = models.BooleanField(default=False)
    individual = models.BooleanField()
    plan = models.IntegerField(choices=Plan.choices, default=Plan.free)

    requests_per_month = models.IntegerField(default=0)
    monthly_requests = models.IntegerField(default=0)
    number_requests = models.IntegerField(default=0)
    date_update = models.DateField(null=True)

    # deprecate #
    owner = models.ForeignKey(User, blank=True, null=True)
    max_users = models.IntegerField(default=3)
    monthly_cost = models.IntegerField(default=10000)
    stripe_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Autogenerates the slug based on the org name"""
        self.slug = slugify(self.name)
        super(Organization, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse('org-detail', kwargs={'slug': self.slug})

    def has_member(self, user):
        """Is the user a member of this organization?"""
        # XXX test
        return self.users.filter(pk=user.pk).exists()

    @transaction.atomic
    def update_data(self, data):
        """Set updated data from squarelet"""
        # XXX calc reqs/month to see if max users changed
        if self.plan != data['plan']:
            # do the things to change the plan
            pass
        if self.date_update != data['date_update']:
            # do the re-up
            pass
        fields = [
            'name', 'slug', 'individual', 'private', 'plan', 'date_update'
        ]
        for field in fields:
            setattr(self, field, data[field])
        self.save()

    def _set_subscription(self, plan, max_users):
        """Update data for when the subscription has changed"""
        if self.plan == Plan.free and plan != Plan.free:
            # create a subscription going from free to non-free
            self._create_subscription(plan, max_users)
        elif self.plan != Plan.free and plan == Plan.free:
            # cancel a subscription going from non-free to free
            self._cancel_subscription()
        elif self.plan != Plan.free and plan != Plan.free:
            # modify a subscription going from non-free to non-free
            self._modify_subscription(plan, max_users)

    def _create_subscription(self, plan, max_users):
        """Set values for new subscription"""
        extra_users = max_users - MIN_USERS[plan]
        requests_per_month = (
            BASE_REQUESTS[plan] + extra_users * EXTRA_REQUESTS_PER_USER[plan]
        )
        self.requests_per_month = requests_per_month
        self.monthly_requests = requests_per_month

    def _cancel_subscription(self):
        """Reset values for a cancelled subscription"""
        self.requests_per_month = 0
        self.date_update = None

    def _modify_subscription(self, plan, max_users):
        """Set values for a modified subscription"""

        extra_users = max_users - MIN_USERS[plan]
        requests_per_month = (
            BASE_REQUESTS[plan] + extra_users * EXTRA_REQUESTS_PER_USER[plan]
        )

        # if new limit is higher than the old limit, add them immediately
        # use f expressions to avoid race conditions
        self.monthly_requests = F("monthly_requests") + Greatest(
            requests_per_month - F("requests_per_month"), 0
        )
        self.requests_per_month = requests_per_month

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
            # XXX catching this?
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


class Membership(models.Model):
    """Through table for organization membership"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='memberships'
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='memberships'
    )
    active = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "organization")

    def __unicode__(self):
        return u"{} in {}".format(self.user, self.organization)
