"""
Tasks for the messages application.
"""

# Django
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.contrib.auth.models import User
from django.utils import timezone

# Standard Library
import logging
from random import randint

# Third Party
import stripe
from dateutil.relativedelta import relativedelta
from requests.exceptions import RequestException

# MuckRock
from muckrock.accounts.models import Profile, RecurringDonation
from muckrock.core.utils import stripe_retry_on_error
from muckrock.crowdfund.models import RecurringCrowdfundPayment
from muckrock.message import digests, receipts
from muckrock.message.email import TemplateEmail
from muckrock.message.notifications import SlackNotification
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)


@task(
    time_limit=600,
    soft_time_limit=570,
    name='muckrock.message.tasks.send_activity_digest',
)
def send_activity_digest(user, subject, interval):
    """Individual task to create and send an activity digest to a user."""
    logger.info(
        'Starting activity digest at: %s User: %s Subject: %s Interval: %s',
        timezone.now(), user, subject, interval
    )
    try:
        email = digests.ActivityDigest(
            user=user,
            subject=subject,
            interval=interval,
        )
        email.send()
    except SoftTimeLimitExceeded:
        logger.error(
            'Send Activity Digest took too long. '
            'User: %s, Subject: %s, Interval %s', user, subject, interval
        )


def send_digests(preference, subject, interval):
    """Helper to send out timed digests"""
    users = (
        User.objects.filter(
            profile__email_pref=preference,
            notifications__read=False,
        ).distinct()
    )
    for user in users:
        send_activity_digest.delay(user, subject, interval)


# every hour
@periodic_task(
    run_every=crontab(hour='*/1', minute=0),
    name='muckrock.message.tasks.hourly_digest'
)
def hourly_digest():
    """Send out hourly digest"""
    send_digests('hourly', u'Hourly Digest', relativedelta(hours=1))


# every day at 10am
@periodic_task(
    run_every=crontab(hour=10, minute=0),
    name='muckrock.message.tasks.daily_digest'
)
def daily_digest():
    """Send out daily digest"""
    send_digests('daily', u'Daily Digest', relativedelta(days=1))


# every Monday at 10am
@periodic_task(
    run_every=crontab(day_of_week=1, hour=10, minute=0),
    name='muckrock.message.tasks.weekly_digest'
)
def weekly_digest():
    """Send out weekly digest"""
    send_digests('weekly', u'Weekly Digest', relativedelta(weeks=1))


# first day of every month at 10am
@periodic_task(
    run_every=crontab(day_of_month=1, hour=10, minute=0),
    name='muckrock.message.tasks.monthly_digest'
)
def monthly_digest():
    """Send out monthly digest"""
    send_digests('monthly', u'Monthly Digest', relativedelta(months=1))


# every day at 9:30am
@periodic_task(
    run_every=crontab(hour=9, minute=30),
    name='muckrock.message.tasks.staff_digest'
)
def staff_digest():
    """Send out staff digest"""
    staff_users = User.objects.filter(is_staff=True).distinct()
    for staff_user in staff_users:
        email = digests.StaffDigest(
            user=staff_user, subject=u'Daily Staff Digest'
        )
        email.send()


@task(name='muckrock.message.tasks.send_invoice_receipt')
def send_invoice_receipt(invoice_id):
    """Send out a receipt for an invoiced charge"""
    invoice = stripe_retry_on_error(
        stripe.Invoice.retrieve,
        invoice_id,
    )
    try:
        charge = stripe_retry_on_error(
            stripe.Charge.retrieve,
            invoice.charge,
        )
    except stripe.error.InvalidRequestError:
        # a free subscription has no charge attached
        # maybe send a notification about the renewal
        # but for now just handle the error
        return

    try:
        customer = stripe_retry_on_error(
            stripe.Customer.retrieve,
            invoice.customer,
        )
        charge.metadata['email'] = customer.email
    except stripe.error.InvalidRequestError:
        logger.error('Could not retrieve customer')
        return

    plan = get_subscription_type(invoice)
    if plan == 'donate':
        receipt_function = receipts.donation_receipt
    elif plan.startswith('crowdfund'):
        receipt_function = receipts.crowdfund_payment_receipt
        charge.metadata['crowdfund_id'] = plan.split('-')[1]
        recurring_payment = RecurringCrowdfundPayment.objects.filter(
            subscription_id=invoice.subscription,
        ).first()
        if recurring_payment:
            recurring_payment.log_payment(charge)
        else:
            logger.error(
                'No recurring crowdfund payment for: %s',
                invoice.subscription,
            )
    else:
        # other types are handled by squarelet
        return

    receipt = receipt_function(None, charge)
    receipt.send(fail_silently=False)


@task(name='muckrock.message.tasks.send_charge_receipt')
def send_charge_receipt(charge_id):
    """Send out a receipt for a charge"""
    logger.info('Charge Receipt for %s', charge_id)
    charge = stripe_retry_on_error(
        stripe.Charge.retrieve,
        charge_id,
    )
    # if the charge was generated by an invoice, let the invoice handler send the receipt
    if charge.invoice:
        return
    # we should expect charges to have metadata attached when they are made
    try:
        user_email = charge.metadata['email']
        user_action = charge.metadata['action']
    except KeyError:
        # squarelet charges will not have matching metadata
        logger.warning('Malformed charge metadata, no receipt sent: %s', charge)
        return
    # try getting the user based on the provided email
    # we know from Checkout purchases that logged in users have their email autofilled
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        user = None
    logger.info('Charge Receipt User: %s', user)
    try:
        receipt_functions = {
            'crowdfund-payment': receipts.crowdfund_payment_receipt,
            'donation': receipts.donation_receipt,
        }
        receipt_function = receipt_functions[user_action]
    except KeyError:
        # squarelet charges will be handled on squarelet
        logger.warning('Unrecognized charge: %s', user_action)
        receipt_function = receipts.generic_receipt
    receipt = receipt_function(user, charge)
    receipt.send(fail_silently=False)


def get_subscription_type(invoice):
    """Gets the subscription type from the invoice."""
    # get the first line of the invoice
    if invoice.lines.total_count > 0:
        return invoice.lines.data[0].plan.id
    else:
        return 'unknown'


@task(name='muckrock.message.tasks.failed_payment')
def failed_payment(invoice_id):
    """Notify a customer about a failed subscription invoice."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    invoice = stripe_retry_on_error(
        stripe.Invoice.retrieve,
        invoice_id,
    )
    attempt = invoice.attempt_count
    subscription_type = get_subscription_type(invoice)
    recurring_donation = None
    crowdfund = None
    if subscription_type == 'donate':
        recurring_donation = RecurringDonation.objects.filter(
            subscription_id=invoice.subscription,
        ).first()
        if recurring_donation:
            user = recurring_donation.user
            recurring_donation.payment_failed = True
            recurring_donation.save()
        else:
            user = None
            logger.error(
                'No recurring crowdfund found for %s',
                invoice.subscription,
            )
    elif subscription_type.startswith('crowdfund'):
        recurring_payment = RecurringCrowdfundPayment.objects.filter(
            subscription_id=invoice.subscription,
        ).first()
        if recurring_payment:
            user = recurring_payment.user
            crowdfund = recurring_payment.crowdfund
            recurring_payment.payment_failed = True
            recurring_payment.save()
        else:
            user = None
            logger.error(
                'No recurring crowdfund found for %s',
                invoice.subscription,
            )
    else:
        # squarelet handles other types
        return
    subject = u'Your payment has failed'
    context = {
        'attempt': attempt,
        'type': subscription_type,
        'crowdfund': crowdfund,
    }
    if subscription_type.startswith('crowdfund'):
        context['type'] = 'crowdfund'
    if attempt == 4:
        # on last attempt, cancel the user's subscription and lower the failed payment flag
        if subscription_type == 'donate' and recurring_donation:
            recurring_donation.cancel()
        elif subscription_type.startswith('crowdfund') and recurring_payment:
            recurring_payment.cancel()
        logger.info(
            '%s subscription has been cancelled due to failed payment', user
        )
        subject = u'Your %s subscription has been cancelled' % subscription_type
        context['attempt'] = 'final'
    else:
        logger.info('Failed payment by %s, attempt %s', user, attempt)
    notification = TemplateEmail(
        user=user,
        extra_context=context,
        text_template='message/notification/failed_payment.txt',
        html_template='message/notification/failed_payment.html',
        subject=subject,
    )
    notification.send(fail_silently=False)


@task(name='muckrock.message.tasks.support')
def support(user, message, _task):
    """Send a response to a user about a task."""
    context = {'message': message, 'task': _task}
    notification = TemplateEmail(
        user=user,
        extra_context=context,
        text_template='message/notification/support.txt',
        html_template='message/notification/support.html',
        subject=u'Support #%d' % _task.id
    )
    notification.send(fail_silently=False)


@task(name='muckrock.message.tasks.notify_project_contributor')
def notify_project_contributor(user, project, added_by):
    """Notify a user that they were added as a contributor to a project."""
    context = {'project': project, 'added_by': added_by}
    notification = TemplateEmail(
        user=user,
        extra_context=context,
        text_template='message/notification/project.txt',
        html_template='message/notification/project.html',
        subject=u'Added to a project'
    )
    notification.send(fail_silently=False)


@task(name='muckrock.message.tasks.slack')
def slack(payload):
    """Send a Slack notification using the provided payload."""
    try:
        notification = SlackNotification(payload)
        notification.send(fail_silently=False)
    except RequestException as exc:
        slack.retry(
            countdown=2 ** slack.request.retries * 30 + randint(0, 30),
            args=[payload],
            exc=exc,
        )


@task(name='muckrock.message.tasks.gift')
def gift(to_user, from_user, gift_description):
    """Notify the user when they have been gifted requests."""
    context = {'from': from_user, 'gift': gift_description}
    notification = TemplateEmail(
        user=to_user,
        extra_context=context,
        text_template='message/notification/gift.txt',
        html_template='message/notification/gift.html',
        subject=u'You got a gift!'
    )
    notification.send(fail_silently=False)
