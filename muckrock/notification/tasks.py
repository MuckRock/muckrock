"""
Tasks for the notifications application.
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from celery.schedules import crontab
from celery.task import periodic_task, task
import logging

from muckrock.accounts.models import Profile
from muckrock.notification.messages import DailyNotification, FailedPaymentNotification
from muckrock.notification import receipts

logger = logging.getLogger(__name__)

@periodic_task(run_every=crontab(hour=10, minute=0),
               name='muckrock.notification.tasks.daily_notification')
def daily_notification():
    """Send out daily notifications"""
    profiles_to_notify = Profile.objects.filter(email_pref='daily').distinct()
    for profile in profiles_to_notify:
        # for now, only send staff the new updates
        if profile.user.is_staff:
            email = DailyNotification(profile.user)
            email.send()
        else:
            profile.send_notifications()

@task(name='muckrock.notification.tasks.send_receipt')
def send_receipt(event_data):
    """Send out a receipt for a charge"""
    # we should expect charges to have metadata assigned
    try:
        user_email = event_data['metadata']['email']
        user_action = event_data['metadata']['action']
    except KeyError:
        logger.warning('Malformed event metadata, so no receipt sent: %s', event_data)
        return
    # try getting the user based on the provided email
    # we know from Checkout purchases that logged in users have their email autofilled
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        user = None
    # every charge type has a corresponding receipt class
    receipt_classes = {
        'request-purchase': receipts.RequestPurchaseReceipt,
        'request-fee': receipts.RequestFeeReceipt,
        'request-multi': receipts.MultiRequestReceipt,
        'crowdfund-payment': receipts.CrowdfundPaymentReceipt,
        'pro-subscription': receipts.ProSubscriptionReceipt,
        'org-subscription': receipts.OrgSubscriptionReceipt
    }
    try:
        receipt_class = receipt_classes[user_action]
    except KeyError:
        receipt_class = receipts.GenericReceipt
    receipt = receipt_class(user, event_data)
    receipt.send(fail_silently=False)

@task(name='muckrock.notification.tasks.failed_payment')
def failed_payment(event_data):
    """Notify a customer about a failed subscription invoice."""
    attempt = event_data['attempt_count']
    # invoices should always have a customer, so we can infer the user from that
    customer = event_data['customer']
    user = get_object_or_404(User, customer_id=customer)
    if attempt == 4:
        # on last attempt, cancel the user's subscription
        user.profile.cancel_pro_subscription()
        logger.info('%s subscription has been cancelled due to failed payment', user.username)
        notification = FailedPaymentNotification(user, 'final')
        notification.send(fail_silently=False)
    else:
        logger.info('Failed payment by %s, attempt %s', user.username, attempt)
        notification = FailedPaymentNotification(user, attempt)
        notification.send(fail_silently=False)
