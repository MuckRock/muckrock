"""
Models for the organization application
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils.text import slugify

from muckrock.settings import MONTHLY_REQUESTS

from datetime import date
import logging
import stripe

logger = logging.getLogger(__name__)

class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    owner = models.ForeignKey(User)
    date_update = models.DateField(null=True)
    num_requests = models.IntegerField(default=0)
    max_users = models.IntegerField(default=3)
    monthly_cost = models.IntegerField(default=10000)
    monthly_requests = models.IntegerField(default=MONTHLY_REQUESTS.get('org', 0))
    stripe_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Autogenerates the slug based on the org name"""
        self.slug = slugify(self.name)
        super(Organization, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('org-detail', [], {'slug': self.slug})

    def restore_requests(self):
        """Restore the number of requests credited to the org."""
        if self.active:
            self.date_update = date.today()
            self.num_requests = self.monthly_requests
            self.save()
        return

    def get_requests(self):
        """
        Get the number of requests left for this month.
        Before doing so, restore the org's requests if they have not
        been restored for this month, or ever.
        """
        if self.date_update:
            not_this_month = self.date_update.month != date.today().month
            not_this_year = self.date_update.year != date.today().year
            if not_this_month or not_this_year:
                self.restore_requests()
        else:
            self.restore_requests()
        return self.num_requests

    def is_owned_by(self, user):
        """Returns true IFF the passed-in user is the owner of the org"""
        return self.owner == user

    def has_member(self, user):
        """Returns true IFF the passed-in user is a member of the org"""
        if user.profile in self.members.all():
            return True
        else:
            return False

    def send_email_notification(self, user, subject, template):
        """Notifies a user via email about a change to their organization membership."""
        msg = render_to_string(template, {
            'member_name': user.first_name,
            'organization_name': self.name,
            'organization_owner': self.owner.get_full_name(),
            'organization_link': self.get_absolute_url()
        })
        email = EmailMessage(
            subject=subject,
            body=msg,
            from_email='info@muckrock.com',
            to=[user.email],
            bcc=['diagnostics@muckrock.com']
        )
        email.send(fail_silently=False)
        return

    def update_monthly_cost(self, num_seats):
        """Changes the monthly cost to $20 times the number of seats, which can be negative."""
        price_per_user = 2000
        current_monthly_cost = self.monthly_cost
        seat_difference = num_seats - self.max_users
        cost_adjustment = price_per_user * seat_difference
        self.monthly_cost = current_monthly_cost + cost_adjustment
        self.save()
        return self.monthly_cost

    def update_monthly_requests(self, num_seats):
        """Changes the monthly requests to 10 times the number of seats, which can be negative."""
        requests_per_user = 10
        current_requests = self.monthly_requests
        seat_difference = num_seats - self.max_users
        request_adjustment = requests_per_user * seat_difference
        self.monthly_requests = current_requests + request_adjustment
        self.save()
        return self.monthly_requests

    def add_member(self, user):
        """
        Adds the passed-in user as a member of the organization.
        If the user is already a member of the organization, it does nothing.
        """
        if self.members.count() == self.max_users:
            raise ValueError('No open seats for adding members.')
        if self.has_member(user):
            logger.error(('Could not add %s as a member to the organization %s, '
                          'as they are already a member.'), user.username, self.name)
            return
        user.profile.organization = self
        user.profile.save()
        logger.info('%s was added as a member of the organization %s', user.username, self.name)
        self.send_email_notification(
            user,
            '[MuckRock] You were added to an organization',
            'text/organization/add_member.txt')
        return

    def remove_member(self, user):
        """
        Remove a user (who isn't the owner) from this organization.
        If the user is the owner or isn't a member, raise an error.
        """
        if self.is_owned_by(user) or not self.has_member(user):
            error_msg = 'Cannot remove %s from organization %s' % (user.username, self.name)
            logger.error(error_msg)
            raise ValueError(error_msg)
        user.profile.organization = None
        user.profile.save()
        logger.info('%s was removed as a member of the %s organization.', user.username, self.name)
        self.send_email_notification(
            user,
            '[MuckRock] You were removed from an organization',
            'text/organization/remove_member.txt')
        return

    def activate_subscription(self, num_seats):
        """Subscribes the owner to the org plan, given a variable quantity"""
        # pylint: disable=no-member
        self.update_monthly_cost(num_seats)
        self.update_monthly_requests(num_seats)
        quantity = self.monthly_cost/100
        customer = self.owner.profile.customer()
        subscription = customer.subscriptions.create(plan='org', quantity=quantity)
        # if the owner has a pro account, downgrade them to a community account
        if self.owner.profile.acct_type == 'pro':
            self.owner.profile.acct_type = 'community'
            self.owner.profile.save()
        self.max_users = num_seats
        self.stripe_id = subscription.id
        self.active = True
        self.save()
        return

    def update_subscription(self, num_seats):
        """Updates the quantity of the subscription, but only if the subscription is active"""
        # pylint: disable=no-member
        if self.active != True:
            raise AttributeError('Cannot update an inactive organization.')
        self.update_monthly_cost(num_seats)
        self.update_monthly_requests(num_seats)
        quantity = self.monthly_cost/100
        customer = self.owner.profile.customer()
        subscription = customer.subscriptions.retrieve(self.stripe_id)
        try:
            subscription.quantity = quantity
            subscription = subscription.save()
        except stripe.InvalidRequestError:
            logger.error(('No subscription is associated with organization '
                         'owner %s.'), self.owner.username)
        self.max_users = num_seats
        self.stripe_id = subscription.id
        self.save()
        return

    def cancel_subscription(self):
        """Cancels the owner's subscription to this org's plan"""
        # pylint: disable=no-member
        customer = self.owner.profile.customer()
        subscription = customer.subscriptions.retrieve(self.stripe_id)
        try:
            subscription.delete()
        except stripe.InvalidRequestError:
            logger.error(('No subscription is associated with organization '
                         'owner %s.'), self.owner.username)
        self.stripe_id = ''
        self.active = False
        self.save()
        return
