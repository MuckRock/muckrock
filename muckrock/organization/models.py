"""
Models for the organization application
"""

# Django
from django.conf import settings
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
from muckrock.core.utils import squarelet_get, squarelet_post
from muckrock.foia.exceptions import InsufficientRequestsError

logger = logging.getLogger(__name__)
stripe.api_version = '2015-10-16'


class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""
    # pylint: disable=too-many-instance-attributes

    name = models.CharField(max_length=255, unique=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    users = models.ManyToManyField(
        User, through="organization.Membership", related_name='organizations'
    )
    private = models.BooleanField(default=False)
    individual = models.BooleanField()
    org_type = models.IntegerField()

    # deprecate #
    slug = models.SlugField(max_length=255, blank=True)

    owner = models.ForeignKey(User, blank=True, null=True)

    date_update = models.DateField(auto_now_add=True, null=True)
    num_requests = models.IntegerField(default=0)
    max_users = models.IntegerField(default=3)
    monthly_cost = models.IntegerField(default=10000)
    _monthly_requests = models.IntegerField(
        default=settings.MONTHLY_REQUESTS.get('org', 0),
        db_column='monthly_requests',
    )
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

    @property
    def squarelet(self):
        """Get info on this organization from squarelet"""
        # XXX make sure we are checking for squarelet errors in callers
        resp = squarelet_get('/api/organizations/{}/'.format(self.uuid))
        if resp.status_code == requests.codes.ok:
            return resp.json()
        else:
            raise SquareletError()

    @property
    def number_requests(self):
        """Get the number of ala carte requests left from squarelet"""
        return self.squarelet['number_requests']

    @property
    def monthly_requests(self):
        """Get the number of monthly reccuring requests left from squarelet"""
        return self.squarelet['monthly_requests']

    def make_requests(self, amount):
        """Try to deduct requests from the organization's balance"""
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

    class Meta:
        unique_together = ("user", "organization")

    def __unicode__(self):
        return u"{} in {}".format(self.user, self.organization)
