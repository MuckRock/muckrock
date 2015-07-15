"""
Models for the organization application
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.utils.text import slugify

from muckrock.settings import MONTHLY_REQUESTS

from datetime import date, timedelta
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
    max_users = models.IntegerField(default=50)
    monthly_cost = models.IntegerField(default=45000)
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

    def is_active(self):
        """Is this organization active?"""
        return self.active

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

    def add_member(self, user):
        """
        Adds the passed-in user as a member of the organization.
        If the user is already a member of the organization, it does nothing.
        """
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
        If the user isn't a member of the organization, do nothing.
        If the user is the owner, raise an error.
        """
        if not self.has_member(user):
            logger.error(('Cannot remove user %s from the organization %s, as they '
                'are not a member of the organization.'), user.username, self.name)
            return
        if self.is_owned_by(user):
            error_msg = ('Cannot remove user %s from the organization %s, as they '
                'are the owner of the organization.') % (user.username, self.name)
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

    def create_plan(self):
        """
        Creates an org-specific Stripe plan and saves it to the org.
        Returns the id associated with the plan.
        Raises an exception if the org already has a plan.
        """
        if self.stripe_id:
            error_msg = ('This organization already has an associated plan. '
                         'Delete the existing plan before adding a new one.')
            raise ValueError(error_msg)
        plan_name = self.name + ' Plan'
        plan_id = self.slug + '-org-plan'
        plan = stripe.Plan.create(
            amount=self.monthly_cost,
            interval='month',
            name=plan_name,
            currency='usd',
            id=plan_id)
        self.stripe_id = plan.id
        self.save()
        return self.stripe_id

    def delete_plan(self):
        """Deletes this organization's specific Stripe plan"""
        if not self.stripe_id:
            raise ValueError('This organization has no associated plan to cancel.')
        try:
            plan = stripe.Plan.retrieve(self.stripe_id)
            plan.delete()
        except stripe.InvalidRequestError:
            logger.error(('No Plan is associated with Stripe ID %s. '
                'Removing the Stripe ID from the organization anyway.'), self.stripe_id)
        self.stripe_id = ''
        self.save()
        return

    def update_plan(self):
        """
        Deletes and recreates an organization's plan.
        Plans must be deleted and recreated because Stripe prohibits plans
        from updating any information except their name.
        """
        if not self.stripe_id:
            raise ValueError(('This organization has no associated plan to update. '
                              'Try creating a plan instead.'))
        self.delete_plan()
        self.create_plan()
        self.start_subscription()
        return

    def start_subscription(self):
        """Subscribes the owner to this org's plan"""
        # pylint: disable=no-member
        profile = self.owner.profile
        org_plan = stripe.Plan.retrieve(self.stripe_id)
        customer = profile.customer()
        customer.update_subscription(plan=org_plan.id)
        customer.save()
        # if the owner has a pro account, downgrade them to a community account
        if profile.acct_type == 'pro':
            profile.acct_type = 'community'
            profile.save()
        self.active = True
        self.save()
        return

    def pause_subscription(self):
        """Cancels the owner's subscription to this org's plan"""
        # pylint: disable=no-member
        customer = self.owner.profile.customer()
        try:
            customer.cancel_subscription()
            customer.save()
        except stripe.InvalidRequestError:
            logger.error(('No subscription is associated with organization '
                         'owner %s.'), self.owner.username)
        self.active = False
        self.save()
        return
