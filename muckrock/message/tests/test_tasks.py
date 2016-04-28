"""
Tests the messages application tasks.
These will usually tell us if a message
object cannot be instantiated.
"""

from django.test import TestCase

import mock
import nose.tools

from muckrock import factories
from muckrock.message import tasks

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

mock_subscription = mock.Mock()
mock_subscription.id = 'test-pro-subscription'
mock_subscription.plan.id = 'pro'
mock_subscription.save.return_value = mock_subscription
mock_subscription.delete.return_value = mock_subscription
mock_customer = mock.Mock()
mock_customer.id = 'test-customer'
mock_customer.save.return_value = mock_customer
mock_customer.update_subscription.return_value = mock_subscription
mock_customer.cancel_subscription.return_value = mock_subscription
mock_customer.subscriptions.create.return_value = mock_subscription
mock_customer.subscriptions.retrieve.return_value = mock_subscription
MockCustomer = mock.Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer

mock_charge = mock.Mock()
mock_charge.id = 'test-charge'
mock_charge.invoice = False
mock_charge.amount = 100
mock_charge.created = 1446680016
mock_charge.source = {'last4': '1234'}
MockCharge = mock.Mock()
MockCharge.retrieve.return_value = mock_charge

mock_invoice_line_item = mock.Mock()
mock_invoice_line_item.plan.id = mock_subscription.id

mock_invoice = mock.Mock()
mock_invoice.id = 'test-invoice'
mock_invoice.attempt_count = 1
mock_invoice.customer = mock_customer.id
mock_invoice.charge = mock_charge
mock_invoice.lines.total_count = 1
mock_invoice.lines.data = [mock_invoice_line_item]
mock_invoice.subscription = mock_subscription
MockInvoice = mock.Mock()
MockInvoice.retrieve.return_value = mock_invoice


class TestDailyTask(TestCase):
    """Tests the daily email notification task."""
    def setUp(self):
        # create an experimental user to notify about an activity
        # right now special emails are limited to experimental only
        factories.UserFactory(profile__experimental=True)
        factories.UserFactory()

    @mock.patch('muckrock.message.digests.ActivityDigest.send')
    @mock.patch('muckrock.accounts.models.Profile.send_notifications')
    def test_daily_notification_task(self, mock_profile_send, mock_send):
        """Make sure the send method is called for the experimental user."""
        # pylint: disable=no-self-use
        tasks.daily_digest()
        mock_send.assert_called_with()
        mock_profile_send.assert_called_with()


class TestStaffTask(TestCase):
    """Tests the daily staff digest task."""
    def setUp(self):
        self.staff_user = factories.UserFactory(is_staff=True)

    @mock.patch('muckrock.message.digests.StaffDigest.send')
    def test_staff_digest_task(self, mock_send):
        """Make sure the send method is called with the staff user."""
        # pylint: disable=no-self-use
        tasks.staff_digest()
        mock_send.assert_called_with()


@mock.patch('muckrock.message.email.TemplateEmail.send')
class TestNotificationTasks(TestCase):
    """Email notifications are sent to users upon key events."""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_welcome(self, mock_send):
        """Welcomes a new user to the site."""
        tasks.welcome(self.user)
        mock_send.assert_called_with(fail_silently=False)

    def test_gift(self, mock_send):
        """Tells the user when they have been given a gift."""
        sender = factories.UserFactory()
        gift = '4 requests'
        tasks.gift(self.user, sender, gift)
        mock_send.assert_called_with(fail_silently=False)


class TestEmailChangeTask(TestCase):
    """Tests the email change notification."""
    def setUp(self):
        self.user = factories.UserFactory()

    @mock.patch('muckrock.message.notifications.EmailChangeNotification.send')
    def test_email_change_task(self, mock_send):
        """Make sure the notification is actually sent."""
        tasks.email_change(self.user, 'old.email@email.com')
        mock_send.assert_called_with(fail_silently=False)


@mock.patch('stripe.Charge', MockCharge)
class TestSendChargeReceiptTask(TestCase):
    """Tests the send charge receipt task."""
    # pylint: disable=no-self-use

    def setUp(self):
        self.user = factories.UserFactory()
        mock_charge.invoice = None
        mock_charge.metadata = {
            'email': self.user.email
        }

    @mock.patch('muckrock.message.receipts.RequestPurchaseReceipt.send')
    def test_request_purchase_receipt(self, mock_send):
        """A receipt should be sent after request bundle is purchased."""
        mock_charge.metadata['action'] = 'request-purchase'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.RequestFeeReceipt.send')
    def test_request_fee_receipt(self, mock_send):
        """A receipt should be sent after request fee is paid."""
        foia = factories.FOIARequestFactory()
        mock_charge.metadata['action'] = 'request-fee'
        mock_charge.metadata['foia'] = foia.pk
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.MultiRequestReceipt.send')
    def test_multirequest_receipt(self, mock_send):
        """A receipt should be sent after a multi-request is purchased."""
        mock_charge.metadata['action'] = 'request-multi'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.CrowdfundPaymentReceipt.send')
    def test_crowdfund_payment_receipt(self, mock_send):
        """A receipt should be sent after a crowdfund payment is made."""
        mock_charge.metadata['action'] = 'crowdfund-payment'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.GenericReceipt.send')
    def test_other_receipt(self, mock_send):
        """A generic receipt should be sent for any other charges."""
        mock_charge.metadata['action'] = 'unknown-charge'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.GenericReceipt.send')
    def test_invoice_charge(self, mock_send):
        """A charge with an attachced invoice should not generate an email."""
        mock_charge.invoice = mock_invoice.id
        mock_charge.metadata['action'] = 'unknown-charge'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_not_called()


@mock.patch('stripe.Invoice', MockInvoice)
@mock.patch('stripe.Charge', MockCharge)
@mock.patch('stripe.Customer', MockCustomer)
class TestSendInvoiceReceiptTask(TestCase):
    """Invoice receipts are send when an invoice payment succeeds."""
    # pylint: disable=no-self-use

    @mock.patch('muckrock.message.receipts.ProSubscriptionReceipt.send')
    def test_pro_invoice_receipt(self, mock_send):
        """A receipt should be sent after a pro subscription payment is made."""
        mock_subscription.plan.id = 'pro'
        customer_id = 'test-pro'
        factories.ProfileFactory(customer_id=customer_id)
        mock_invoice.customer = customer_id
        tasks.send_invoice_receipt(mock_invoice.id)
        mock_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.receipts.OrgSubscriptionReceipt.send')
    def test_org_invoice_receipt(self, mock_send):
        """A receipt should be sent after an org subscription payment is made."""
        mock_subscription.plan.id = 'org'
        customer_id = 'test-org'
        owner = factories.UserFactory(profile__customer_id=customer_id)
        factories.OrganizationFactory(owner=owner)
        mock_invoice.customer = customer_id
        tasks.send_invoice_receipt(mock_invoice.id)
        mock_send.assert_called_with(fail_silently=False)


@mock.patch('stripe.Invoice', MockInvoice)
class TestFailedPaymentTask(TestCase):
    """Tests the failed payment task."""

    def setUp(self):
        mock_invoice.plan.id = 'pro'
        mock_invoice.attempt_count = 1
        self.profile = factories.ProfileFactory(customer_id=mock_invoice.customer)

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    def test_failed_invoice_charge(self, mock_send):
        """Make sure the send method is called for a failed payment notification"""
        tasks.failed_payment(mock_invoice.id)
        mock_send.assert_called_with(fail_silently=False)
        self.profile.refresh_from_db()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    @mock.patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_last_attempt_pro(self, mock_cancel, mock_send):
        """After the last attempt at payment, cancel the user's pro subscription"""
        self.profile.payment_failed = True
        self.profile.save()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')
        mock_invoice.attempt_count = 4
        mock_invoice.lines.data[0].plan.id = 'pro'
        tasks.failed_payment(mock_invoice.id)
        self.profile.refresh_from_db()
        mock_cancel.assert_called_with()
        mock_send.assert_called_with(fail_silently=False)
        ok_(not self.profile.payment_failed, 'The payment failed flag should be lowered.')

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    @mock.patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_last_attempt_org(self, mock_cancel, mock_send):
        """After the last attempt at payment, cancel the user's org subscription"""
        self.profile.payment_failed = True
        self.profile.save()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')
        factories.OrganizationFactory(owner=self.profile.user)
        mock_invoice.attempt_count = 4
        mock_invoice.lines.data[0].plan.id = 'org'
        tasks.failed_payment(mock_invoice.id)
        self.profile.refresh_from_db()
        mock_cancel.assert_called_with()
        mock_send.assert_called_with(fail_silently=False)
        ok_(not self.profile.payment_failed, 'The payment failed flag should be lowered.')
