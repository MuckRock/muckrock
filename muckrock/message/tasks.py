"""
Tasks for the messages application.
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from celery.schedules import crontab
from celery.task import periodic_task, task
import logging
import stripe

from muckrock.accounts.models import Profile
from muckrock.message import notifications, receipts
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)

@periodic_task(run_every=crontab(hour=10, minute=0),
               name='muckrock.message.tasks.daily_notification')
def daily_notification():
    """Send out daily notifications"""
    profiles_to_notify = Profile.objects.filter(email_pref='daily').distinct()
    for profile in profiles_to_notify:
        # for now, only send staff the new updates
        if profile.user.is_staff:
            email = notifications.DailyNotification(profile.user)
            email.send()
        else:
            profile.send_notifications()

@task(name='muckrock.message.tasks.send_invoice_receipt')
def send_invoice_receipt(invoice_id):
    """Send out a receipt for an invoiced charge"""
    invoice = stripe.Invoice.retrieve(invoice_id)
    try:
        charge = stripe.Charge.retrieve(invoice.charge)
    except stripe.error.InvalidRequestError:
        # a free subscription has no charge attached
        # maybe send a notification about the renewal
        # but for now just handle the error
        return
    profile = Profile.objects.get(customer_id=invoice.customer)
    # send a receipt based on the plan
    customer = profile.customer()
    subscription = customer.subscriptions.retrieve(invoice.subscription)
    try:
        receipt_classes = {
            'pro': receipts.ProSubscriptionReceipt,
            'org': receipts.OrgSubscriptionReceipt
        }
        receipt_class = receipt_classes[subscription.plan.id]
    except KeyError:
        logger.warning('Invoice charged for unrecognized plan: %s', subscription.plan.name)
        receipt_class = receipts.GenericReceipt
    receipt = receipt_class(profile.user, charge)
    receipt.send(fail_silently=False)

@task(name='muckrock.message.tasks.send_charge_receipt')
def send_charge_receipt(charge_id):
    """Send out a receipt for a charge"""
    charge = stripe.Charge.retrieve(charge_id)
    # if the charge was generated by an invoice, let the invoice handler send the receipt
    if charge.invoice:
        return
    # we should expect charges to have metadata attached when they are made
    try:
        user_email = charge.metadata['email']
        user_action = charge.metadata['action']
    except KeyError:
        logger.warning('Malformed charge metadata, no receipt sent: %s', charge)
        return
    # try getting the user based on the provided email
    # we know from Checkout purchases that logged in users have their email autofilled
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        user = None
    # every charge type should have a corresponding receipt class
    # if there is a charge type without a class, fallback to a generic receipt
    # this list of receipt classes should be made into a setting...later
    try:
        receipt_classes = {
            'request-purchase': receipts.RequestPurchaseReceipt,
            'request-fee': receipts.RequestFeeReceipt,
            'request-multi': receipts.MultiRequestReceipt,
            'crowdfund-payment': receipts.CrowdfundPaymentReceipt,
        }
        receipt_class = receipt_classes[user_action]
    except KeyError:
        receipt_class = receipts.GenericReceipt
    receipt = receipt_class(user, charge)
    receipt.send(fail_silently=False)

def get_subscription_type(invoice):
    """Gets the subscription type from the invoice."""
    # get the first line of the invoice
    lines = invoice.lines
    subscription_type = 'unknown'
    if lines.total_count > 0:
        data = lines.data
        plan = data[0].plan
        subscription_type = plan.id
    return subscription_type

@task(name='muckrock.message.tasks.failed_payment')
def failed_payment(invoice_id):
    """Notify a customer about a failed subscription invoice."""
    invoice = stripe.Invoice.retrieve(invoice_id)
    attempt = invoice.attempt_count
    subscription_type = get_subscription_type(invoice)
    profile = Profile.objects.get(customer_id=invoice.customer)
    user = profile.user
    # raise the failed payment flag on the profile
    profile.payment_failed = True
    profile.save()
    if attempt == 4:
        # on last attempt, cancel the user's subscription and lower the failed payment flag
        if subscription_type == 'pro':
            profile.cancel_pro_subscription()
        elif subscription_type == 'org':
            org = Organization.objects.get(owner=user)
            org.cancel_subscription()
        profile.payment_failed = False
        profile.save()
        logger.info('%s subscription has been cancelled due to failed payment', user.username)
        context = {
            'attempt': 'final',
            'type': subscription_type
        }
    else:
        logger.info('Failed payment by %s, attempt %s', user.username, attempt)
        context = {
            'attempt': attempt,
            'type': subscription_type
        }
    notification = notifications.FailedPaymentNotification(user, context)
    notification.send(fail_silently=False)

@task(name='muckrock.message.tasks.welcome')
def welcome(user):
    """Send a welcome notification to a new user. Hello!"""
    verification_url = reverse('acct-verify-email')
    key = user.profile.generate_confirmation_key()
    context = {'verification_link': user.profile.wrap_url(verification_url, key=key)}
    notification = notifications.WelcomeNotification(user, context)
    notification.send(fail_silently=False)

@task(name='muckrock.message.tasks.gift')
def gift(to_user, from_user, gift_description):
    """Notify the user when they have been gifted requests."""
    context = {
        'from': from_user,
        'gift': gift_description
    }
    notification = notifications.GiftNotification(to_user, context)
    notification.send(fail_silently=False)
