"""
Models for the organization application
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils.text import slugify

from datetime import date
import logging
import stripe

logger = logging.getLogger(__name__)
stripe.api_version = '2015-10-16'

class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""
    # pylint: disable=too-many-instance-attributes

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    owner = models.ForeignKey(User)
    date_update = models.DateField(auto_now_add=True, null=True)
    num_requests = models.IntegerField(default=0)
    max_users = models.IntegerField(default=3)
    monthly_cost = models.IntegerField(default=10000)
    monthly_requests = models.IntegerField(default=settings.MONTHLY_REQUESTS.get('org', 0))
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

    def update_num_seats(self, num_seats):
        """Updates the max users and adjusts the monthly cost and monthly requests in response."""
        # since the compute methods use the current max_seat values, update the max_seats last
        new_cost = self.compute_monthly_cost(num_seats)
        new_requests = self.compute_monthly_requests(num_seats)
        self.monthly_cost = new_cost
        self.monthly_requests = new_requests
        self.max_users = num_seats
        self.save()

    def compute_monthly_cost(self, num_seats):
        """Computes the monthly cost given the number of seats, which can be negative."""
        price_per_user = settings.ORG_PRICE_PER_SEAT
        current_monthly_cost = self.monthly_cost
        seat_difference = num_seats - self.max_users
        cost_adjustment = price_per_user * seat_difference
        return current_monthly_cost + cost_adjustment

    def compute_monthly_requests(self, num_seats):
        """Computes the monthly requests given the number of seats, which can be negative."""
        requests_per_user = settings.ORG_REQUESTS_PER_SEAT
        current_requests = self.monthly_requests
        seat_difference = num_seats - self.max_users
        request_adjustment = requests_per_user * seat_difference
        return current_requests + request_adjustment

    def add_member(self, user):
        """Adds the given user as a member of the organization."""
        added = False
        if not self.active:
            raise AttributeError('Cannot add members to an inactive organization.')
        if self.members.count() == self.max_users:
            raise AttributeError('No open seat for new members.')
        if user.profile.organization:
            which_org = 'this' if user.profile.organization == self else 'a different'
            raise AttributeError('%s is already a member of %s organization.' %
                (user.first_name, which_org)
            )
        is_an_owner = Organization.objects.filter(owner=user).exists()
        owns_this_org = self.is_owned_by(user)
        if is_an_owner and not owns_this_org:
            user_name = user.first_name
            raise AttributeError('%s is already an owner of a different organization.' % user_name)
        if not self.has_member(user):
            user.profile.organization = self
            user.profile.save()
            self.send_email_notification(
                user,
                '[MuckRock] You were added to an organization',
                'text/organization/add_member.txt'
            )
            added = True
        return added

    def remove_member(self, user):
        """Removes the given user from this organization if they are a member."""
        removed = False
        if self.has_member(user):
            user.profile.organization = None
            user.profile.save()
            self.send_email_notification(
                user,
                '[MuckRock] You were removed from an organization',
                'text/organization/remove_member.txt'
            )
            removed = True
        return removed

    def activate_subscription(self, token, num_seats):
        """Subscribes the owner to the org plan, given a variable quantity"""
        # pylint: disable=no-member
        if self.active:
            raise AttributeError('Cannot activate an active organization.')
        if num_seats < settings.ORG_MIN_SEATS:
            raise ValueError('Cannot have an organization with less than three member seats.')

        quantity = self.compute_monthly_cost(num_seats)/100
        customer = self.owner.profile.customer()
        subscription = customer.subscriptions.create(
            plan='org',
            source=token,
            quantity=quantity
        )
        self.update_num_seats(num_seats)
        self.num_requests = self.monthly_requests
        self.stripe_id = subscription.id
        self.active = True
        self.save()

        # If the owner has a pro account, cancel it.
        # Assume the pro user has an active subscription.
        # On the off chance that they don't, just silence the error.
        if self.owner.profile.acct_type == 'pro':
            try:
                self.owner.profile.cancel_pro_subscription()
            except AttributeError:
                pass
        self.owner.profile.subscription_id = subscription.id
        self.owner.profile.save()
        return subscription

    def update_subscription(self, num_seats):
        """Updates the quantity of the subscription, but only if the subscription is active"""
        # pylint: disable=no-member
        if not self.active:
            raise AttributeError('Cannot update an inactive subscription.')
        if num_seats < settings.ORG_MIN_SEATS:
            raise ValueError('Cannot have an organization with less than three member seats.')
        quantity = self.compute_monthly_cost(num_seats)/100
        customer = self.owner.profile.customer()
        try:
            subscription = customer.subscriptions.retrieve(self.stripe_id)
            subscription.quantity = quantity
            subscription = subscription.save()
            self.stripe_id = subscription.id
            self.owner.profile.subscription_id = subscription.id
        except stripe.InvalidRequestError:
            logger.error(('No subscription is associated with organization '
                         'owner %s.'), self.owner.username)
            return
        old_monthly_requests = self.monthly_requests
        self.update_num_seats(num_seats)
        new_monthly_requests = self.monthly_requests
        # if it goes up, let it go up. if it goes down, don't let it go down
        if new_monthly_requests > old_monthly_requests:
            self.num_requests += new_monthly_requests - old_monthly_requests
        self.save()
        self.owner.profile.save()
        return subscription

    def cancel_subscription(self):
        """Cancels the owner's subscription to this org's plan"""
        # pylint: disable=no-member
        if not self.active:
            raise AttributeError('Cannot cancel an inactive subscription.')
        customer = self.owner.profile.customer()
        subscription = customer.subscriptions.retrieve(self.stripe_id)
        try:
            subscription = subscription.delete()
            self.stripe_id = ''
            self.owner.profile.subscription_id = ''
            self.owner.profile.payment_failed = False
        except stripe.InvalidRequestError:
            logger.error(('No subscription is associated with organization '
                         'owner %s.'), self.owner.username)
        self.active = False
        self.save()
        self.owner.profile.save()
        return subscription
