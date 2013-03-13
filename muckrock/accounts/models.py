"""
Models for the accounts application
"""

from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField, USStateField
from django.db import models

from datetime import datetime
import stripe

from muckrock.foia.models import FOIARequest
from muckrock.settings import MONTHLY_REQUESTS, STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

class Profile(models.Model):
    """User profile information for muckrock"""

    acct_types = (
        ('admin', 'Admin'),
        ('beta', 'Beta'),
        ('community', 'Community'),
        ('pro', 'Professional'),
    )

    user = models.ForeignKey(User, unique=True)
    address1 = models.CharField(max_length=50, blank=True, verbose_name='address')
    address2 = models.CharField(max_length=50, blank=True, verbose_name='address (line 2)')
    city = models.CharField(max_length=60, blank=True)
    state = USStateField(blank=True, default='MA')
    zip_code = models.CharField(max_length=10, blank=True)
    phone = PhoneNumberField(blank=True)
    follows = models.ManyToManyField(FOIARequest, related_name='followed_by', blank=True)
    acct_type = models.CharField(max_length=10, choices=acct_types)

    # paid for requests
    num_requests = models.IntegerField(default=0)
    # for limiting # of requests / month
    monthly_requests = models.IntegerField(default=0)
    date_update = models.DateField()

    # for stripe
    stripe_id = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return u"%s's Profile" % unicode(self.user).capitalize()

    def get_monthly_requests(self):
        """Get the number of requests left for this month"""

        if self.date_update.month != datetime.now().month or \
                self.date_update.year != datetime.now().year:
            # update requests if they have not yet been updated this month
            self.date_update = datetime.now()
            self.monthly_requests = MONTHLY_REQUESTS.get(self.acct_type, 0)
            self.save()

        return self.monthly_requests

    def make_request(self):
        """Reduce one from the user's request amount"""

        if self.get_monthly_requests() > 0:
            self.monthly_requests -= 1
            self.save()
            return True
        elif self.num_requests > 0:
            self.num_requests -= 1
            self.save()
            return True
        else:
            return False

    def can_embargo(self):
        """Is this user allowed to embargo?"""

        return self.acct_type in ['admin', 'beta', 'pro']

    def can_view_emails(self):
        """Is this user allowed to view all emails and private contact information?"""

        return self.acct_type in ['admin', 'pro']

    def get_cc(self):
        """Get the user's CC if they have one on file"""
        return getattr(self.get_customer(), 'active_card', None)

    def save_cc(self, token):
        """Save a credit card"""
        customer = self.get_customer()
        customer.card = token
        customer.save()

    def get_customer(self):
        """Get stripe customer"""
        try:
            customer = stripe.Customer.retrieve(self.stripe_id)
        except stripe.InvalidRequestError:
            customer = self.save_customer()

        return customer

    def save_customer(self, token=None):
        """Save stripe customer"""
        # pylint: disable=E1101

        if token:
            customer = stripe.Customer.create(
                description=self.user.username,
                email=self.user.email,
                card=token,
                plan='pro')
        else:
            customer = stripe.Customer.create(
                description=self.user.username,
                email=self.user.email)

        self.stripe_id = customer.id
        self.save()

        return customer

    def pay(self, form, amount, desc):
        """Create a stripe charge for the user"""
        # pylint: disable=E1101

        customer = self.get_customer()
        desc = '%s: %s' % (self.user.username, desc)
        save_cc = form.cleaned_data.get('save_cc')
        use_on_file = form.cleaned_data.get('use_on_file')
        token = form.cleaned_data.get('token')

        if not use_on_file and save_cc:
            self.save_cc(token)

        if use_on_file or save_cc:
            stripe.Charge.create(amount=amount, currency='usd', customer=customer.id,
                                 description=desc)
        else:
            stripe.Charge.create(amount=amount, currency='usd', card=token,
                                 description=desc)


class Statistics(models.Model):
    """Nightly statistics"""

    date = models.DateField()

    total_requests = models.IntegerField()
    total_requests_success = models.IntegerField()
    total_requests_denied = models.IntegerField()
    total_requests_draft = models.IntegerField(null=True)
    total_requests_submitted = models.IntegerField(null=True)
    total_requests_awaiting_response = models.IntegerField(null=True)
    total_requests_awaiting_appeal = models.IntegerField(null=True)
    total_requests_fix_required = models.IntegerField(null=True)
    total_requests_payment_required = models.IntegerField(null=True)
    total_requests_no_docs = models.IntegerField(null=True)
    total_requests_partial = models.IntegerField(null=True)
    total_requests_abandoned = models.IntegerField(null=True)

    total_pages = models.IntegerField()
    total_users = models.IntegerField()
    users_today = models.ManyToManyField(User)
    total_agencies = models.IntegerField()
    total_fees = models.IntegerField()

    pro_users = models.IntegerField(null=True)
    pro_user_names = models.TextField(blank=True)

    total_page_views = models.IntegerField(null=True)

    daily_requests_pro = models.IntegerField(null=True)
    daily_requests_community = models.IntegerField(null=True)
    daily_requests_beta = models.IntegerField(null=True)
    daily_articles = models.IntegerField(null=True)

    class Meta:
        # pylint: disable=R0903
        ordering = ['-date']
