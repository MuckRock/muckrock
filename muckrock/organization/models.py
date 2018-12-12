"""
Models for the organization application
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

# Standard Library
import logging
from uuid import uuid4

# Third Party
import requests
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
    slug = models.SlugField(max_length=255, blank=True)  # XXX
    private = models.BooleanField(default=False)
    individual = models.BooleanField()
    plan = models.IntegerField(choices=Plan.choices, default=Plan.free)

    requests_per_month = models.IntegerField(default=0)
    monthly_requests = models.IntegerField(default=0)
    number_requests = models.IntegerField(default=0)

    # deprecate #
    owner = models.ForeignKey(User, blank=True, null=True)
    date_update = models.DateField(auto_now_add=True, null=True)
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

    def update_data(self, data):
        """Set updated data from squarelet"""
        fields = ['name', 'slug', 'plan', 'individual', 'private']
        for field in fields:
            setattr(self, field, data[field])
        self.save()

    def make_requests(self, amount):
        """Try to deduct requests from the organization's balance"""
        # XXX redo this
        resp = squarelet_post(
            '/api/organizations/{}/requests/'.format(self.uuid), {
                'amount': amount
            }
        )
        if resp.status_code == requests.codes.payment:
            raise InsufficientRequestsError(resp.json()['extra'])
        elif resp.status_code != requests.codes.ok:
            raise SquareletError()
        else:
            return resp.json()

    def return_requests(self, amounts):
        """Return requests to the organization's balance"""
        # XXX redo this
        # XXX async this? error check?
        squarelet_post(
            '/api/organizations/{}/requests/'.format(self.uuid), {
                'return_regular': amounts['regular'],
                'return_monthly': amounts['monthly'],
            }
        )


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
