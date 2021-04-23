"""
Models for the crowdfund application
"""

# Django
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

# Standard Library
import logging
from datetime import date, timedelta
from decimal import Decimal

# Third Party
import stripe

# MuckRock
from muckrock.accounts.utils import stripe_get_customer
from muckrock.core.utils import new_action, stripe_retry_on_error
from muckrock.message.email import TemplateEmail

stripe.api_version = "2015-10-16"
logger = logging.getLogger(__name__)


class CrowdfundQuerySet(models.QuerySet):
    """Query set for crowdfunds"""

    def filter_by_entitlement(self, entitlement):
        """Filter for Crowdfunds by users with a certain entitlement type"""
        return self.filter(
            Q(foia__composer__organization__entitlement__slug=entitlement)
            | Q(projects__contributors__organizations__entitlement__slug=entitlement)
        )


class Crowdfund(models.Model):
    """Crowdfunding campaign"""

    objects = CrowdfundQuerySet.as_manager()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    payment_capped = models.BooleanField(default=False)
    payment_required = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00"
    )
    payment_received = models.DecimalField(
        max_digits=14, decimal_places=2, default="0.00"
    )
    date_due = models.DateField(blank=True, null=True)
    date_created = models.DateField(
        # Only allow null's since this wasn't on here to begin with
        blank=True,
        null=True,
        default=date.today,
    )
    closed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse("crowdfund", kwargs={"pk": self.pk})

    def expired(self):
        """Has this crowdfund run out of time?"""
        if self.closed:
            return True
        elif self.date_due is not None:
            return date.today() >= self.date_due
        else:
            return False

    def amount_remaining(self):
        """Reports the amount still needed to be raised as a decimal."""
        return Decimal(self.payment_required) - Decimal(self.payment_received)

    def percent_funded(self):
        """Reports the percent of the amount required that has been funded."""
        if self.payment_required == 0:
            return 100
        else:
            return int(self.payment_received / self.payment_required * 100)

    def update_payment_received(self):
        """Combine the amounts of all the payments"""
        self.payment_received = self.payments.aggregate(total=Sum("amount"))["total"]
        self.save()
        if self.payment_received >= self.payment_required and self.payment_capped:
            self.close_crowdfund(succeeded=True)

    def close_crowdfund(self, succeeded=False):
        """Close the crowdfund and create a new task for it once it reaches its goal."""
        self.closed = True
        self.save()
        self.crowdfundtask_set.create()
        verb = "ended"
        if succeeded:
            logger.info("Crowdfund %d reached its goal.", self.id)
            verb = "succeeded"
        new_action(self, verb)

    def contributors_count(self):
        """Return a count of all the contributors to a crowdfund"""
        return self.payments.count()

    def anonymous_contributors_count(self):
        """Return a count of anonymous contributors"""
        return self.payments.filter(Q(show=False) | Q(user=None)).count()

    def named_contributors(self):
        """Return unique named contributors only."""
        # returns the list of a set of a list to remove duplicates
        return (
            User.objects.filter(
                crowdfundpayment__crowdfund=self, crowdfundpayment__show=True
            )
            .select_related("profile")
            .distinct()
        )

    def get_crowdfund_object(self):
        """Is this for a request or a project?"""
        if hasattr(self, "foia"):
            return self.foia
        elif self.project:
            return self.project
        else:
            raise ValueError("Exactly one of foia or project should be set")

    def make_payment(self, token, email, amount, show=False, user=None):
        """Creates a payment for the crowdfund"""
        # pylint: disable=too-many-arguments
        amount = Decimal(amount)
        if self.payment_capped and amount > self.amount_remaining():
            amount = self.amount_remaining()
        # Try processing the payment using Stripe.
        # If the payment fails, do not catch the error.
        # Stripe represents currency as smallest-unit integers.
        stripe_amount = int(float(amount) * 100)
        charge = stripe_retry_on_error(
            stripe.Charge.create,
            amount=stripe_amount,
            source=token,
            currency="usd",
            metadata={
                "email": email,
                "action": "crowdfund-payment",
                "crowdfund_id": self.id,
                "crowdfund_name": self.name,
            },
            idempotency_key=True,
        )
        return self.log_payment(amount, user, show, charge)

    def log_payment(self, amount, user, show, charge, recurring=None):
        """Log a payment that was made"""
        # pylint: disable=too-many-arguments
        payment = CrowdfundPayment.objects.create(
            amount=amount,
            crowdfund=self,
            user=user,
            show=show,
            charge_id=charge.id,
            recurring=recurring,
        )
        cache.delete("cf:%s:crowdfund_widget_data" % self.pk)
        logger.info(payment)
        self.update_payment_received()
        return payment

    def make_recurring_payment(self, token, email, amount, show, user):
        """Make a recurring payment for the crowdfund"""
        # pylint: disable=too-many-arguments
        plan = self._get_stripe_plan()
        customer = stripe_get_customer(
            email, "Crowdfund {} for {}".format(self.pk, email)
        )
        subscription = stripe_retry_on_error(
            customer.subscriptions.create,
            plan=plan,
            source=token,
            quantity=amount,
            idempotency_key=True,
        )
        RecurringCrowdfundPayment.objects.create(
            user=user,
            crowdfund=self,
            email=email,
            amount=amount,
            show=show,
            customer_id=customer.id,
            subscription_id=subscription.id,
        )
        return subscription

    def _get_stripe_plan(self):
        """Ensure there is a stripe plan created for this crowdfund"""
        plan = "crowdfund-{}".format(self.pk)
        try:
            stripe_retry_on_error(stripe.Plan.retrieve, plan)
        except stripe.InvalidRequestError:
            # default to $1 (100 cents) and then use the quantity
            # on the subscription to set the amount
            stripe_retry_on_error(
                stripe.Plan.create,
                id=plan,
                amount=100,
                currency="usd",
                interval="month",
                name=self.name,
                statement_descriptor="MuckRock Crowdfund",
            )
        return plan

    def send_intro_email(self, user):
        """Send an intro email to the user upon crowdfund creation"""
        msg = TemplateEmail(
            subject="Crowdfund Campaign Launched",
            user=user,
            bcc=["diagnostics@muckrock", "info@muckrock"],
            text_template="crowdfund/email/intro.txt",
            html_template="crowdfund/email/intro.html",
            extra_context={
                "amount": int(self.payment_required),
                "url": self.get_crowdfund_object().get_absolute_url(),
            },
        )
        msg.send(fail_silently=False)

    @property
    def project(self):
        """Get the project for this crowdfund if it exists"""
        # there will never be more than one project due to unique constraint
        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        if hasattr(self, "_project"):
            return self._project
        projects = self.projects.all()
        if projects:
            self._project = projects[0]
        else:
            self._project = None
        return self._project

    def can_recur(self):
        """Can this crowdfund accept recurring payments?"""
        return not self.payment_capped and self.date_due is None

    def num_donations_yesterday(self):
        """How many donations were made yesterday?"""
        return self.payments.filter(
            date__gte=date.today() - timedelta(1), date__lt=date.today()
        ).count()


class CrowdfundPayment(models.Model):
    """A payment toward a crowdfund campaign"""

    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    show = models.BooleanField(default=False)
    charge_id = models.CharField(max_length=255, blank=True)
    crowdfund = models.ForeignKey(
        Crowdfund, related_name="payments", on_delete=models.CASCADE
    )
    recurring = models.ForeignKey(
        "crowdfund.RecurringCrowdfundPayment",
        related_name="payments",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return "Payment of $%.2f by %s on %s for %s" % (
            self.amount,
            self.user,
            self.date.date(),
            self.crowdfund.get_crowdfund_object(),
        )


class RecurringCrowdfundPayment(models.Model):
    """Keep track of recurring crowdfund payments"""

    user = models.ForeignKey(
        "auth.User",
        blank=True,
        null=True,
        related_name="recurring_crowdfund_payments",
        on_delete=models.SET_NULL,
    )
    crowdfund = models.ForeignKey(
        Crowdfund, related_name="recurring_payments", on_delete=models.CASCADE
    )
    email = models.EmailField()
    amount = models.PositiveIntegerField()
    show = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=255)
    subscription_id = models.CharField(unique=True, max_length=255)
    payment_failed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    deactivated_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Recurring Crowdfund Payment: {} - ${}/Month by {}".format(
            self.crowdfund.name, self.amount, self.email
        )

    def cancel(self):
        """Cancel the recurring donation"""
        self.active = False
        self.deactivated_datetime = timezone.now()
        self.save()
        subscription = stripe_retry_on_error(
            stripe.Subscription.retrieve, self.subscription_id
        )
        stripe_retry_on_error(subscription.delete)

    def log_payment(self, charge):
        """Log an instance of the recurring payment"""
        return self.crowdfund.log_payment(
            self.amount, self.user, self.show, charge, recurring=self
        )
