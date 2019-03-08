"""
Models for the organization application
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models.expressions import F
from django.db.models.functions import Greatest

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
stripe.api_version = '2015-10-16'


class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""
    # pylint: disable=too-many-instance-attributes

    objects = OrganizationQuerySet.as_manager()

    uuid = models.UUIDField(
        'UUID', unique=True, editable=False, default=uuid4, db_index=True
    )

    users = models.ManyToManyField(
        User, through="organization.Membership", related_name='organizations'
    )

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    private = models.BooleanField(default=False)
    individual = models.BooleanField(default=True)
    plan = models.ForeignKey('organization.Plan', null=True)
    card = models.CharField(max_length=255, blank=True)

    requests_per_month = models.IntegerField(
        default=0,
        help_text='How many monthly requests this organization gets each month',
    )
    monthly_requests = models.IntegerField(
        default=0,
        help_text=
        'How many recurring monthly requests are left for this month - these do '
        'not roll over and are just reset to `requests_per_month` on `date_update`'
    )
    number_requests = models.IntegerField(
        default=0,
        help_text=
        'How many individually purchased requests this organization has - '
        'these never expire and are unaffected by the monthly roll over'
    )
    date_update = models.DateField(null=True)

    payment_failed = models.BooleanField(default=False)

    # deprecate #
    owner = models.ForeignKey(User, blank=True, null=True)
    max_users = models.IntegerField(default=3)
    monthly_cost = models.IntegerField(default=10000)
    stripe_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    @property
    def display_name(self):
        """Display 'Personal Accoubnt' for individual organizations"""
        if self.individual:
            return u'Personal Account'
        else:
            return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse('org-detail', kwargs={'slug': self.slug})

    def has_member(self, user):
        """Is the user a member of this organization?"""
        return self.users.filter(pk=user.pk).exists()

    def has_admin(self, user):
        """Is the user an admin of this organization?"""
        return self.users.filter(pk=user.pk, memberships__admin=True).exists()

    def update_data(self, data):
        """Set updated data from squarelet"""

        # plan should always be created on client sites before being used
        # get_or_create is used as a precauitionary measure
        self.plan, created = Plan.objects.get_or_create(
            slug=data['plan'],
            defaults={'name': data['plan'].replace('-', ' ').title()},
        )
        if created:
            logger.warning('Unknown plan: %s', data['plan'])

        # calc reqs/month in case it has changed
        self.requests_per_month = self.plan.requests_per_month(
            data['max_users']
        )

        # if date update has changed, then this is a monthly restore of the
        # subscription, and we should restore monthly requests.  If not, requests
        # per month may have changed if they changed their plan or their user count,
        # in which case we should add the difference to their monthly requests
        # if requests per month increased
        if self.date_update == data['date_update']:
            # add additional monthly requests immediately
            self.monthly_requests = F('monthly_requests') + Greatest(
                self.requests_per_month - F('requests_per_month'), 0
            )
        else:
            # reset monthly requests when date_update is updated
            self.monthly_requests = self.requests_per_month

        # update the remaining fields
        fields = [
            'name',
            'slug',
            'individual',
            'private',
            'date_update',
            'card',
            'payment_failed',
        ]
        for field in fields:
            if field in data:
                setattr(self, field, data[field])
        self.save()

    @transaction.atomic
    def make_requests(self, amount):
        """Try to deduct requests from the organization's balance"""
        request_count = {'monthly': 0, 'regular': 0}
        organization = Organization.objects.select_for_update().get(pk=self.pk)

        request_count['monthly'] = min(amount, organization.monthly_requests)
        amount -= request_count['monthly']

        request_count['regular'] = min(amount, organization.number_requests)
        amount -= request_count['regular']

        if amount > 0:
            raise InsufficientRequestsError(amount)

        organization.monthly_requests -= request_count['monthly']
        organization.number_requests -= request_count['regular']
        organization.save()
        return request_count

    def return_requests(self, amounts):
        """Return requests to the organization's balance"""
        self.monthly_requests = F('monthly_requests') + amounts['monthly']
        self.number_requests = F('number_requests') + amounts['regular']
        self.save()

    def add_requests(self, amount):
        """Add requests"""
        self.number_requests = F('number_requests') + amount
        self.save()

    def pay(self, amount, description, token, save_card):
        """Pay via Squarelet API"""
        resp = squarelet_post(
            '/api/charges/',
            data={
                'organization': self.uuid,
                'amount': amount,
                'description': description,
                'token': token,
                'save_card': save_card,
            }
        )
        logger.info('Squarelet response: %s %s', resp.status_code, resp.content)
        resp.raise_for_status()
        resp_json = resp.json()
        if 'card' in resp_json:
            self.card = resp_json['card']
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


class Plan(models.Model):
    """Plans that organizations can subscribe to"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    minimum_users = models.PositiveSmallIntegerField(default=1)
    base_requests = models.PositiveSmallIntegerField(default=0)
    requests_per_user = models.PositiveSmallIntegerField(default=0)
    feature_level = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.name

    def requests_per_month(self, users):
        """Calculate how many requests an organization gets per month on this plan
        for a given number of users"""
        return (
            self.base_requests +
            (users - self.minimum_users) * self.requests_per_user
        )
