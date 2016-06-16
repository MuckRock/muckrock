"""
Models for the accounts application
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string

from actstream.models import Action
from datetime import datetime
import dbsettings
from easy_thumbnails.fields import ThumbnailerImageField
from itertools import groupby
from localflavor.us.models import PhoneNumberField, USStateField
from lot.models import LOT
import stripe
from urllib import urlencode

from muckrock.utils import generate_key
from muckrock.values import TextValue

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = '2015-10-16'

class EmailOptions(dbsettings.Group):
    """DB settings for sending email"""
    email_footer = TextValue('email footer')

options = EmailOptions()

ACCT_TYPES = [
    ('admin', 'Admin'),
    ('basic', 'Basic'),
    ('beta', 'Beta'),
    ('pro', 'Professional'),
    ('proxy', 'Proxy'),
    ('robot', 'Robot'),
]

PAYMENT_FEE = .05

class Profile(models.Model):
    """User profile information for muckrock"""
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    email_prefs = (
        ('never', 'Never'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )

    user = models.OneToOneField(User)
    address1 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='address'
    )
    address2 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='address (line 2)'
    )
    city = models.CharField(max_length=60, blank=True)
    state = USStateField(
        blank=True,
        help_text=('Your state will be made public on this site.'
                   'If you do not want this information to be public,'
                   ' please leave blank.')
    )
    zip_code = models.CharField(max_length=10, blank=True)
    phone = PhoneNumberField(blank=True)
    acct_type = models.CharField(max_length=10, choices=ACCT_TYPES)
    organization = models.ForeignKey(
        'organization.Organization',
        blank=True,
        null=True,
        related_name='members',
        on_delete=models.SET_NULL)

    # extended information
    profile = models.TextField(blank=True)
    location = models.ForeignKey('jurisdiction.Jurisdiction', blank=True, null=True)
    public_email = models.EmailField(max_length=255, blank=True)
    pgp_public_key = models.TextField(blank=True)
    website = models.URLField(
        max_length=255,
        blank=True,
        help_text='Begin with http://'
    )
    twitter = models.CharField(max_length=255, blank=True)
    linkedin = models.URLField(
        max_length=255,
        blank=True,
        help_text='Begin with http://'
    )
    avatar = ThumbnailerImageField(
        upload_to='account_images',
        blank=True, null=True,
        resize_source={'size': (600, 600), 'crop': 'smart'}
    )

    # provide user access to experimental features
    experimental = models.BooleanField(default=False)
    # email confirmation
    email_confirmed = models.BooleanField(default=False)
    confirmation_key = models.CharField(max_length=24, blank=True)
    # email preferences
    email_pref = models.CharField(
        max_length=10,
        choices=email_prefs,
        default='daily',
        verbose_name='Digest Frequency',
        help_text=('Receive updates on site activity as an emailed digest.')
    )
    use_autologin = models.BooleanField(
        default=True,
        help_text=('Links you receive in emails from us will contain'
                   ' a one time token to automatically log you in')
    )
    # notification preferences
    new_question_notifications = models.BooleanField(default=False)

    # paid for requests
    num_requests = models.IntegerField(default=0)
    # for limiting # of requests / month
    monthly_requests = models.IntegerField(default=0)
    date_update = models.DateField()
    # for Stripe
    customer_id = models.CharField(max_length=255, blank=True)
    subscription_id = models.CharField(max_length=255, blank=True)
    payment_failed = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s's Profile" % unicode(self.user).capitalize()

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('acct-profile', [], {'username': self.user.username})

    def is_advanced(self):
        """Advanced users can access features basic users cannot."""
        advanced_types = ['admin', 'beta', 'pro', 'proxy']
        return self.acct_type in advanced_types or self.is_member_of_active_org()

    def is_member_of(self, organization):
        """Answers whether the profile is a member of the passed organization"""
        return self.organization_id == organization.pk

    def is_member_of_active_org(self):
        """Answers whether the user is a member of an active organization"""
        return self.organization is not None and self.organization.active

    def can_embargo(self):
        """Is this user allowed to embargo?"""
        return self.is_advanced()

    def can_embargo_permanently(self):
        """Is this user allowed to permanently embargo?"""
        return self.acct_type in ['admin'] or self.is_member_of_active_org()

    def can_multirequest(self):
        """Is this user allowed to multirequest?"""
        return self.is_advanced()

    def can_view_emails(self):
        """Is this user allowed to view all emails and private contact information?"""
        return self.is_advanced()

    def get_monthly_requests(self):
        """Get the number of requests left for this month"""
        not_this_month = self.date_update.month != datetime.now().month
        not_this_year = self.date_update.year != datetime.now().year
        # update requests if they have not yet been updated this month
        if not_this_month or not_this_year:
            self.date_update = datetime.now()
            self.monthly_requests = settings.MONTHLY_REQUESTS.get(self.acct_type, 0)
            self.save()
        return self.monthly_requests

    def total_requests(self):
        """Get sum of paid for requests and monthly requests"""
        org_reqs = self.organization.get_requests() if self.organization else 0
        return self.num_requests + self.get_monthly_requests() + org_reqs

    def make_request(self):
        """Decrement the user's request amount by one"""
        organization = self.organization
        if organization and organization.get_requests() > 0:
            organization.num_requests -= 1
            organization.save()
            return True
        if self.get_monthly_requests() > 0:
            self.monthly_requests -= 1
        elif self.num_requests > 0:
            self.num_requests -= 1
        else:
            return False
        self.save()
        return True

    def multiple_requests(self, num):
        """How many requests of each type would be used for this user to make num requests"""
        request_dict = {
            'org_requests': 0,
            'monthly_requests': 0,
            'reg_requests': 0,
            'extra_requests': 0
        }
        org_reqs = self.organization.get_requests() if self.organization else 0
        if org_reqs > num:
            request_dict['org_requests'] = num
            return request_dict
        else:
            request_dict['org_requests'] = org_reqs
            num -= org_reqs
        monthly = self.get_monthly_requests()
        if monthly > num:
            request_dict['monthly_requests'] = num
            return request_dict
        else:
            request_dict['monthly_requests'] = monthly
            num -= monthly
        if self.num_requests > num:
            request_dict['reg_requests'] = num
            return request_dict
        else:
            request_dict['reg_requests'] = self.num_requests
            request_dict['extra_requests'] = num - self.num_requests
            return request_dict

    def bundled_requests(self):
        """Returns the number of requests the user gets when they buy a bundle."""
        how_many = settings.BUNDLED_REQUESTS[self.acct_type]
        if self.is_member_of_active_org():
            how_many = 5
        return how_many

    def customer(self):
        """Retrieve the customer from Stripe or create one if it doesn't exist. Then return it."""
        # pylint: disable=redefined-variable-type
        try:
            if not self.customer_id:
                raise AttributeError('No Stripe ID')
            customer = stripe.Customer.retrieve(self.customer_id)
        except (AttributeError, stripe.InvalidRequestError):
            customer = stripe.Customer.create(
                description=self.user.username,
                email=self.user.email
            )
            self.customer_id = customer.id
            self.save()
        return customer

    def card(self):
        """Retrieve the default credit card from Stripe, if one exists."""
        card = None
        customer = self.customer()
        if customer.default_source:
            card = customer.sources.retrieve(customer.default_source)
        return card

    def has_subscription(self):
        """Check Stripe to see if this user has any active subscriptions."""
        customer = self.customer()
        return customer.subscriptions.total_count > 0

    def start_pro_subscription(self, token=None):
        """Subscribe this profile to a professional plan. Return the subscription."""
        # create the stripe subscription
        customer = self.customer()
        if self.subscription_id:
            raise AttributeError('Only allowed one active subscription at a time.')
        if not token and not customer.default_source:
            raise AttributeError('No payment method provided for this subscription.')
        subscription = customer.subscriptions.create(plan='pro', source=token)
        customer.save()
        # modify the profile object (should this be part of a webhook callback?)
        self.subscription_id = subscription.id
        self.acct_type = 'pro'
        self.date_update = datetime.now()
        self.monthly_requests = settings.MONTHLY_REQUESTS.get('pro', 0)
        self.save()
        return subscription

    def cancel_pro_subscription(self):
        """Unsubscribe this profile from a professional plan. Return the cancelled subscription."""
        customer = self.customer()
        # subscription reference either exists as a saved field or inside the Stripe customer
        # if it isn't, then they probably don't have a subscription
        if not self.subscription_id and not len(customer.subscriptions.data) > 0:
            raise AttributeError('There is no subscription to cancel.')
        if self.subscription_id:
            subscription_id = self.subscription_id
        else:
            subscription_id = customer.subscriptions.data[0].id
        subscription = customer.subscriptions.retrieve(subscription_id)
        subscription = subscription.delete()
        customer = customer.save()
        self.subscription_id = ''
        self.acct_type = 'basic'
        self.monthly_requests = settings.MONTHLY_REQUESTS.get('basic', 0)
        self.payment_failed = False
        self.save()
        return subscription

    def pay(self, token, amount, metadata, fee=PAYMENT_FEE):
        """
        Creates a Stripe charge for the user.
        Should always expect a 1-cent based integer (e.g. $1.00 = 100)
        Should apply a baseline fee (5%) to all payments.
        """
        # pylint: disable=no-self-use
        modified_amount = int(amount + (amount * fee))
        if not metadata.get('email') or not metadata.get('action'):
            raise ValueError('The charge metadata is malformed.')
        stripe.Charge.create(
            amount=modified_amount,
            currency='usd',
            source=token,
            metadata=metadata
        )

    def generate_confirmation_key(self):
        """Generate random key used for validating the email address"""
        key = generate_key(24)
        self.confirmation_key = key
        self.save()
        return key

    def notify(self, action):
        """Notify a user about an action"""
        Notification.objects.create(user=self.user, action=action)

    def send_notifications(self):
        """Send unread notifications from queue to user"""

        subjects = {
            'done': "you've got new MuckRock docs!",
            'partial': "you've got new MuckRock docs!",
            'rejected': 'an agency rejected a MuckRock request - appeal?',
            'fix': 'we need help fixing a MuckRock request.',
            'payment': 'an agency wants payment for a MuckRock request.'
        }
        category = {
            'done': 'Completed Requests',
            'partial': 'Completed Requests',
            'rejected': 'Rejected Requests',
            'fix': 'Requests Needing Action',
            'payment': 'Requests Needing Action',
            'no_docs': 'No Responsive Documents',
        }
        status_order = ['done', 'partial', 'rejected', 'fix', 'payment',
                        'no_docs', 'abandoned', 'appealing', 'started',
                        'submitted', 'ack', 'processed']

        def get_subject(status, total_foias):
            """Get subject for a given status"""
            if status in subjects:
                return subjects[status]
            elif total_foias > 1:
                return '%d MuckRock requests have updates' % total_foias
            else:
                return 'a MuckRock request has been updated'

        foias = sorted(
            self.notifications.all(),
            key=lambda f: status_order.index(f.status) if f.status in status_order else 100
        )
        grouped_foias = list((s, list(fs)) for s, fs in groupby(
            foias,
            lambda f: category.get(f.status, 'Recently Updated Requests')
        ))
        if not grouped_foias:
            return
        if len(grouped_foias) == 1:
            subject = '%s, %s' % (
                self.user.first_name,
                get_subject(grouped_foias[0][1][0].status, len(foias))
            )
        else:
            subject = '%s, %s  Plus, %s' % (
                self.user.first_name,
                get_subject(grouped_foias[0][1][0].status, len(foias)),
                get_subject(grouped_foias[1][1][0].status, len(foias))
            )

        msg = render_to_string('text/user/notify_mail.txt', {
            'name': self.user.get_full_name(),
            'foias': grouped_foias,
            'footer': options.email_footer
        })
        email = EmailMessage(
            subject=subject,
            body=msg,
            from_email='info@muckrock.com',
            to=[self.user.email],
            bcc=['diagnostics@muckrock.com']
        )
        email.send(fail_silently=False)

        self.notifications.clear()

    def wrap_url(self, link, **extra):
        """Wrap a URL for autologin"""
        if self.use_autologin:
            lot = LOT.objects.create(
                user=self.user,
                type='slow-login',
                )
            extra.update({settings.LOT_MIDDLEWARE_PARAM_NAME: lot.uuid})
        return link + '?' + urlencode(extra)


class NotificationQuerySet(models.QuerySet):
    """Object manager for notifications"""
    def for_user(self, user):
        """All notifications for a user"""
        return self.filter(user=user)

    def for_model(self, model):
        """All notifications for a model. Requires filtering the action."""
        model_ct = ContentType.objects.get_for_model(model)
        actor = models.Q(action__actor_content_type=model_ct)
        action_object = models.Q(action__action_object_content_type=model_ct)
        target = models.Q(action__target_content_type=model_ct)
        return self.filter(actor|action_object|target)

    def for_object(self, object):
        """All notifications for an object. Requires filtering the action."""
        object_pk = object.pk
        object_ct = ContentType.objects.get_for_model(object)
        actor = models.Q(
            action__actor_content_type=object_ct,
            action__actor_object_id=object_pk)
        action_object = models.Q(
            action__action_object_content_type=object_ct,
            action__action_object_object_id=object_pk)
        target = models.Q(
            action__target_content_type=object_ct,
            action__target_object_id=object_pk)
        return self.filter(actor|action_object|target)

    def get_unread(self):
        """All unread notifications"""
        return self.filter(read=False)


class Notification(models.Model):
    """A notification connects an action to a user."""
    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='notifications')
    action = models.ForeignKey(Action)
    read = models.BooleanField(default=False)
    objects = NotificationQuerySet.as_manager()

    def mark_read(self):
        self.read = True
        self.save()

    def mark_unread(self):
        self.read = False
        self.save()


class Statistics(models.Model):
    """Nightly statistics"""
    # pylint: disable=invalid-name
    date = models.DateField()
    total_requests = models.IntegerField(null=True, blank=True)
    total_requests_success = models.IntegerField(null=True, blank=True)
    total_requests_denied = models.IntegerField(null=True, blank=True)
    total_requests_draft = models.IntegerField(null=True, blank=True)
    total_requests_submitted = models.IntegerField(null=True, blank=True)
    total_requests_awaiting_ack = models.IntegerField(null=True, blank=True)
    total_requests_awaiting_response = models.IntegerField(null=True, blank=True)
    total_requests_awaiting_appeal = models.IntegerField(null=True, blank=True)
    total_requests_fix_required = models.IntegerField(null=True, blank=True)
    total_requests_payment_required = models.IntegerField(null=True, blank=True)
    total_requests_no_docs = models.IntegerField(null=True, blank=True)
    total_requests_partial = models.IntegerField(null=True, blank=True)
    total_requests_abandoned = models.IntegerField(null=True, blank=True)
    requests_processing_days = models.IntegerField(null=True, blank=True)

    orphaned_communications = models.IntegerField(null=True, blank=True)

    total_agencies = models.IntegerField(null=True, blank=True)
    stale_agencies = models.IntegerField(null=True, blank=True)
    unapproved_agencies = models.IntegerField(null=True, blank=True)

    total_pages = models.IntegerField(null=True, blank=True)
    total_users = models.IntegerField(null=True, blank=True)
    users_today = models.ManyToManyField(User)
    total_fees = models.IntegerField(null=True, blank=True)
    pro_users = models.IntegerField(null=True, blank=True)
    pro_user_names = models.TextField(blank=True)
    total_page_views = models.IntegerField(null=True, blank=True)
    daily_requests_pro = models.IntegerField(null=True, blank=True)
    daily_requests_basic = models.IntegerField(null=True, blank=True)
    daily_requests_beta = models.IntegerField(null=True, blank=True)
    daily_requests_proxy = models.IntegerField(null=True, blank=True)
    daily_requests_admin = models.IntegerField(null=True, blank=True)
    daily_requests_org = models.IntegerField(null=True, blank=True)
    daily_articles = models.IntegerField(null=True, blank=True)

    # Task statistics
    total_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_tasks = models.IntegerField(null=True, blank=True)
    total_generic_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_generic_tasks = models.IntegerField(null=True, blank=True)
    total_orphan_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_orphan_tasks = models.IntegerField(null=True, blank=True)
    total_snailmail_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_snailmail_tasks = models.IntegerField(null=True, blank=True)
    total_rejected_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_rejected_tasks = models.IntegerField(null=True, blank=True)
    total_staleagency_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_staleagency_tasks = models.IntegerField(null=True, blank=True)
    total_flagged_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_flagged_tasks = models.IntegerField(null=True, blank=True)
    total_newagency_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_newagency_tasks = models.IntegerField(null=True, blank=True)
    total_response_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_response_tasks = models.IntegerField(null=True, blank=True)
    total_faxfail_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_faxfail_tasks = models.IntegerField(null=True, blank=True)
    total_payment_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_payment_tasks = models.IntegerField(null=True, blank=True)
    total_crowdfundpayment_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_crowdfundpayment_tasks = models.IntegerField(null=True, blank=True)
    daily_robot_response_tasks = models.IntegerField(null=True, blank=True)

    # Org stats
    total_active_org_members = models.IntegerField(null=True, blank=True)
    total_active_orgs = models.IntegerField(null=True, blank=True)

    # notes
    public_notes = models.TextField(default='', blank=True)
    admin_notes = models.TextField(default='', blank=True)

    def __unicode__(self):
        return 'Stats for %s' % self.date

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['-date']
        verbose_name_plural = 'statistics'
