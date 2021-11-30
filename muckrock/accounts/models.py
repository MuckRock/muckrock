"""
Models for the accounts application
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Max
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from django.urls import reverse
from django.utils import timezone

# Standard Library
import logging
from urllib.parse import urlencode
from uuid import uuid4

# Third Party
import requests
import stripe
from actstream.models import Action
from localflavor.us.models import USStateField
from memoize import mproperty
from phonenumber_field.modelfields import PhoneNumberField

# MuckRock
from muckrock.accounts.querysets import ProfileQuerySet
from muckrock.core.utils import cache_get_or_set, squarelet_get, stripe_retry_on_error
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = "2015-10-16"

ACCT_TYPES = [
    ("admin", "Admin"),
    ("basic", "Basic"),
    ("beta", "Beta"),
    ("pro", "Professional"),
    ("proxy", "Proxy"),
    ("robot", "Robot"),
    ("agency", "Agency"),
]

PAYMENT_FEE = 0.05


class Profile(models.Model):
    """User profile information for muckrock"""

    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    objects = ProfileQuerySet.as_manager()

    email_prefs = (
        ("never", "Never"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    )

    user = models.OneToOneField(User, on_delete=models.PROTECT)
    full_name = models.CharField(max_length=255, blank=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4, db_index=True)
    source = models.CharField(
        max_length=20, blank=True, choices=(("foia machine", "FOIA Machine"),)
    )

    address1 = models.CharField(max_length=50, blank=True, verbose_name="address")
    address2 = models.CharField(
        max_length=50, blank=True, verbose_name="address (line 2)"
    )
    city = models.CharField(max_length=60, blank=True)
    state = USStateField(
        blank=True,
        help_text=(
            "Your state will be made public on this site."
            "If you do not want this information to be public,"
            " please leave blank."
        ),
    )
    zip_code = models.CharField(max_length=10, blank=True)
    phone = PhoneNumberField(blank=True)

    # extended information
    profile = models.TextField(blank=True)
    location = models.ForeignKey(
        "jurisdiction.Jurisdiction", blank=True, null=True, on_delete=models.PROTECT
    )
    public_email = models.EmailField(max_length=255, blank=True)
    pgp_public_key = models.TextField(blank=True)
    website = models.URLField(
        max_length=255, blank=True, help_text="Begin with http://"
    )
    twitter = models.CharField(max_length=255, blank=True)
    linkedin = models.URLField(
        max_length=255, blank=True, help_text="Begin with http://"
    )
    avatar_url = models.URLField(max_length=255, blank=True)

    # provide user access to experimental features
    experimental = models.BooleanField(default=False)
    # email confirmation
    email_confirmed = models.BooleanField(default=False)
    # email preferences
    email_pref = models.CharField(
        max_length=10,
        choices=email_prefs,
        default="daily",
        verbose_name="Digest Frequency",
        help_text=("Receive updates on site activity as an emailed digest."),
    )
    use_autologin = models.BooleanField(
        default=True,
        help_text=(
            "Links you receive in emails from us will contain"
            " a one time token to automatically log you in"
        ),
    )
    email_failed = models.BooleanField(default=False)

    # notification preferences
    new_question_notifications = models.BooleanField(default=False)

    # profile preferences
    private_profile = models.BooleanField(
        default=False,
        help_text=("Keep your profile private even if you have filed requests"),
    )

    # deprecate after projects on squarelet #
    org_share = models.BooleanField(
        default=False,
        verbose_name="Share with Organization",
        help_text="Let other members of my organization view my embargoed requests",
    )

    proxy = models.BooleanField(
        default=False, help_text="This user is a proxy filer for their home state"
    )

    # for agency users
    agency = models.OneToOneField(
        "agency.Agency", blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return "%s's Profile" % str(self.user).capitalize()

    def get_absolute_url(self):
        """The url for this object"""
        return reverse("acct-profile", kwargs={"username": self.user.username})

    def is_advanced(self):
        """Advanced users can access features basic users cannot."""
        # pylint: disable=comparison-with-callable
        return self.feature_level > 0

    @mproperty
    def organization(self):
        """Get the user's active organization"""
        return self.user.memberships.get(active=True).organization

    @organization.setter
    def organization(self, organization):
        """Set the user's active organization"""
        if not organization.has_member(self.user):
            raise ValueError(
                "Cannot set a user's active organization to an organization "
                "they are not a member of"
            )
        with transaction.atomic():
            self.user.memberships.filter(active=True).update(active=False)
            self.user.memberships.filter(organization=organization).update(active=True)

    @mproperty
    def individual_organization(self):
        """Get the user's individual organization
        There should always be exactly one individual organization,
        which has a matching UUID
        """
        return Organization.objects.get(uuid=self.uuid)

    @mproperty
    def feature_level(self):
        """The user's highest feature level among all of their organizations"""
        return self.user.organizations.annotate(
            feature_level=Cast(
                KeyTextTransform("feature_level", "entitlement__resources"),
                models.IntegerField(),
            )
        ).aggregate(max=Max("feature_level"))["max"]

    @mproperty
    def is_agency_user(self):
        """Is this an agency user?"""
        return self.agency_id is not None

    def wrap_url(self, link, **extra):
        """Wrap a URL for autologin"""

        link = "{}?{}".format(link, urlencode(extra))

        if not self.use_autologin:
            return "{}{}".format(settings.MUCKROCK_URL, link)

        url_auth_token = self.get_url_auth_token()
        if not url_auth_token:
            # if there was an error getting the auth token from squarelet,
            # just send the email without the autologin links
            return "{}{}".format(settings.MUCKROCK_URL, link)

        muckrock_url = "{}{}?{}".format(
            settings.MUCKROCK_URL, reverse("acct-login"), urlencode({"next": link})
        )
        params = {"next": muckrock_url, "url_auth_token": url_auth_token}
        return "{}/accounts/login/?{}".format(settings.SQUARELET_URL, urlencode(params))

    def get_url_auth_token(self):
        """Get a URL auth token for the user
        Cache it so a single email will use a single auth token"""

        def get_url_auth_token_squarelet():
            """Get the URL auth token from squarelet"""
            try:
                resp = squarelet_get("/api/url_auth_tokens/{}/".format(self.uuid))
                resp.raise_for_status()
            except requests.exceptions.RequestException:
                return None
            return resp.json().get("url_auth_token")

        return cache_get_or_set(
            "url_auth_token:{}".format(self.uuid), get_url_auth_token_squarelet, 10
        )

    def public_profile_page(self):
        """Does this user have a public profile page?"""
        filed_request = self.user.composers.exclude(status="started").count() > 0
        return not self.private_profile and filed_request


class RecurringDonation(models.Model):
    """Keep track of our recurring donations"""

    user = models.ForeignKey(
        User, blank=True, null=True, related_name="donations", on_delete=models.SET_NULL
    )
    email = models.EmailField()
    amount = models.PositiveIntegerField()
    customer_id = models.CharField(max_length=255)
    subscription_id = models.CharField(unique=True, max_length=255)
    payment_failed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    deactivated_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Donation: ${}/Month by {}".format(self.amount, self.email)

    def cancel(self):
        """Cancel the recurring donation"""
        self.active = False
        self.deactivated_datetime = timezone.now()
        self.save()
        subscription = stripe_retry_on_error(
            stripe.Subscription.retrieve, self.subscription_id
        )
        stripe_retry_on_error(subscription.delete)


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
        return self.filter(actor | action_object | target)

    def for_object(self, _object):
        """All notifications for an object. Requires filtering the action."""
        object_pk = _object.pk
        object_ct = ContentType.objects.get_for_model(_object)
        actor = models.Q(
            action__actor_content_type=object_ct, action__actor_object_id=object_pk
        )
        action_object = models.Q(
            action__action_object_content_type=object_ct,
            action__action_object_object_id=object_pk,
        )
        target = models.Q(
            action__target_content_type=object_ct, action__target_object_id=object_pk
        )
        return self.filter(actor | action_object | target)

    def get_unread(self):
        """All unread notifications"""
        return self.filter(read=False)


class Notification(models.Model):
    """A notification connects an action to a user."""

    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, related_name="notifications", on_delete=models.PROTECT
    )
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    objects = NotificationQuerySet.as_manager()

    def __str__(self):
        return "<Notification for %s>" % str(self.user.username).capitalize()

    def mark_read(self):
        """Marks notification as read."""
        self.read = True
        self.save()

    def mark_unread(self):
        """Marks notification as unread."""
        self.read = False
        self.save()


class Statistics(models.Model):
    """Nightly statistics"""

    # pylint: disable=invalid-name
    date = models.DateField()

    # FOIA Requests
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
    total_requests_lawsuit = models.IntegerField(null=True, blank=True)
    requests_processing_days = models.IntegerField(null=True, blank=True)
    total_composers = models.IntegerField(null=True, blank=True)
    total_composers_draft = models.IntegerField(null=True, blank=True)
    total_composers_submitted = models.IntegerField(null=True, blank=True)
    total_composers_filed = models.IntegerField(null=True, blank=True)
    sent_communications_portal = models.IntegerField(null=True, blank=True)
    sent_communications_email = models.IntegerField(null=True, blank=True)
    sent_communications_fax = models.IntegerField(null=True, blank=True)
    sent_communications_mail = models.IntegerField(null=True, blank=True)

    # FOIA Machine Requests
    machine_requests = models.IntegerField(null=True, blank=True)
    machine_requests_success = models.IntegerField(null=True, blank=True)
    machine_requests_denied = models.IntegerField(null=True, blank=True)
    machine_requests_draft = models.IntegerField(null=True, blank=True)
    machine_requests_submitted = models.IntegerField(null=True, blank=True)
    machine_requests_awaiting_ack = models.IntegerField(null=True, blank=True)
    machine_requests_awaiting_response = models.IntegerField(null=True, blank=True)
    machine_requests_awaiting_appeal = models.IntegerField(null=True, blank=True)
    machine_requests_fix_required = models.IntegerField(null=True, blank=True)
    machine_requests_payment_required = models.IntegerField(null=True, blank=True)
    machine_requests_no_docs = models.IntegerField(null=True, blank=True)
    machine_requests_partial = models.IntegerField(null=True, blank=True)
    machine_requests_abandoned = models.IntegerField(null=True, blank=True)
    machine_requests_lawsuit = models.IntegerField(null=True, blank=True)

    orphaned_communications = models.IntegerField(null=True, blank=True)

    total_agencies = models.IntegerField(null=True, blank=True)
    stale_agencies = models.IntegerField(null=True, blank=True)
    unapproved_agencies = models.IntegerField(null=True, blank=True)
    portal_agencies = models.IntegerField(null=True, blank=True)

    total_pages = models.IntegerField(null=True, blank=True)
    total_users = models.IntegerField(null=True, blank=True)
    total_users_excluding_agencies = models.IntegerField(null=True, blank=True)
    total_users_filed = models.IntegerField(null=True, blank=True)
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
    daily_requests_other = models.IntegerField(null=True, blank=True)
    daily_articles = models.IntegerField(null=True, blank=True)

    # Task statistics
    total_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_tasks = models.IntegerField(null=True, blank=True)
    total_generic_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_generic_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_generic_tasks = models.IntegerField(null=True, blank=True)
    total_orphan_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_orphan_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_orphan_tasks = models.IntegerField(null=True, blank=True)
    total_snailmail_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_snailmail_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_snailmail_tasks = models.IntegerField(null=True, blank=True)
    total_rejected_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_rejected_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_rejected_tasks = models.IntegerField(null=True, blank=True)
    total_staleagency_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_staleagency_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_staleagency_tasks = models.IntegerField(null=True, blank=True)
    total_flagged_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_flagged_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_flagged_tasks = models.IntegerField(null=True, blank=True)
    total_newagency_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_newagency_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_newagency_tasks = models.IntegerField(null=True, blank=True)
    total_response_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_response_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_response_tasks = models.IntegerField(null=True, blank=True)
    total_faxfail_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_faxfail_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_faxfail_tasks = models.IntegerField(null=True, blank=True)
    total_payment_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_payment_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_payment_tasks = models.IntegerField(null=True, blank=True)
    total_crowdfundpayment_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_crowdfundpayment_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_crowdfundpayment_tasks = models.IntegerField(null=True, blank=True)
    total_reviewagency_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_reviewagency_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_reviewagency_tasks = models.IntegerField(null=True, blank=True)
    total_portal_tasks = models.IntegerField(null=True, blank=True)
    total_unresolved_portal_tasks = models.IntegerField(null=True, blank=True)
    total_deferred_portal_tasks = models.IntegerField(null=True, blank=True)
    daily_robot_response_tasks = models.IntegerField(null=True, blank=True)
    flag_processing_days = models.IntegerField(null=True, blank=True)
    unresolved_snailmail_appeals = models.IntegerField(null=True, blank=True)

    # Org stats
    total_active_org_members = models.IntegerField(null=True, blank=True)
    total_active_orgs = models.IntegerField(null=True, blank=True)

    # notes
    public_notes = models.TextField(default="", blank=True)
    admin_notes = models.TextField(default="", blank=True)

    # crowdfund
    total_crowdfunds = models.IntegerField(null=True, blank=True)
    total_crowdfunds_pro = models.IntegerField(null=True, blank=True)
    total_crowdfunds_basic = models.IntegerField(null=True, blank=True)
    total_crowdfunds_beta = models.IntegerField(null=True, blank=True)
    total_crowdfunds_proxy = models.IntegerField(null=True, blank=True)
    total_crowdfunds_admin = models.IntegerField(null=True, blank=True)
    open_crowdfunds = models.IntegerField(null=True, blank=True)
    open_crowdfunds_pro = models.IntegerField(null=True, blank=True)
    open_crowdfunds_basic = models.IntegerField(null=True, blank=True)
    open_crowdfunds_beta = models.IntegerField(null=True, blank=True)
    open_crowdfunds_proxy = models.IntegerField(null=True, blank=True)
    open_crowdfunds_admin = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_0 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_0_25 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_25_50 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_50_75 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_75_100 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_100_125 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_125_150 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_150_175 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_175_200 = models.IntegerField(null=True, blank=True)
    closed_crowdfunds_200 = models.IntegerField(null=True, blank=True)

    total_crowdfund_payments = models.IntegerField(null=True, blank=True)
    total_crowdfund_payments_loggedin = models.IntegerField(null=True, blank=True)
    total_crowdfund_payments_loggedout = models.IntegerField(null=True, blank=True)

    # projects
    public_projects = models.IntegerField(null=True, blank=True)
    private_projects = models.IntegerField(null=True, blank=True)
    unapproved_projects = models.IntegerField(null=True, blank=True)
    crowdfund_projects = models.IntegerField(null=True, blank=True)
    project_users = models.IntegerField(null=True, blank=True)
    project_users_pro = models.IntegerField(null=True, blank=True)
    project_users_basic = models.IntegerField(null=True, blank=True)
    project_users_beta = models.IntegerField(null=True, blank=True)
    project_users_proxy = models.IntegerField(null=True, blank=True)
    project_users_admin = models.IntegerField(null=True, blank=True)

    # exemptions
    total_exemptions = models.IntegerField(null=True, blank=True)
    total_invoked_exemptions = models.IntegerField(null=True, blank=True)
    total_example_appeals = models.IntegerField(null=True, blank=True)

    # crowdsources
    total_crowdsources = models.IntegerField("total assignments", null=True, blank=True)
    total_draft_crowdsources = models.IntegerField(
        "total draft assignments", null=True, blank=True
    )
    total_open_crowdsources = models.IntegerField(
        "total open assignments", null=True, blank=True
    )
    total_close_crowdsources = models.IntegerField(
        "total close assignments", null=True, blank=True
    )
    num_crowdsource_responded_users = models.IntegerField(
        "num assignment responded users", null=True, blank=True
    )
    total_crowdsource_responses = models.IntegerField(
        "total assignment responses", null=True, blank=True
    )
    crowdsource_responses_pro = models.IntegerField(
        "assignment responses pro", null=True, blank=True
    )
    crowdsource_responses_basic = models.IntegerField(
        "assignment responses basic", null=True, blank=True
    )
    crowdsource_responses_beta = models.IntegerField(
        "assignment responses beta", null=True, blank=True
    )
    crowdsource_responses_proxy = models.IntegerField(
        "assignment responses proxy", null=True, blank=True
    )
    crowdsource_responses_admin = models.IntegerField(
        "assignment responses admin", null=True, blank=True
    )

    def __str__(self):
        return "Stats for %s" % self.date

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "statistics"
