"""
Tests the messages application.
"""

from django.test import TestCase

import actstream
import logging
import mock
import nose.tools

from muckrock import factories
from muckrock.message import digests, notifications, tasks

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

mock_subscription = mock.Mock()
mock_subscription.id = 'test-pro-subscription'
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
MockInvoice = mock.Mock()
MockInvoice.retrieve.return_value = mock_invoice


class TestDailyDigest(TestCase):
    """Tests the daily digest notification object. It extends Django's built-in email classes."""
    def setUp(self):
        self.user = factories.UserFactory()
        self.digest = digests.DailyDigest

    def test_init(self):
        """The email should create when given a User."""
        ok_(self.digest(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        # pylint:disable=no-self-use
        self.digest(None)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = self.digest(self.user)
        eq_(email.send(), 0)

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user)
        actstream.action.send(other_user, verb='acted')
        # generate the email, which should contain the generated action
        email = self.digest(self.user)
        logging.debug(email.notification_count)
        eq_(email.send(), 1)

    def test_notification_composition(self):
        """The email should be composed of updates to requests I own and things I follow."""
        # lets create a FOIA to belong to our user
        foia = factories.FOIARequestFactory(user=self.user)
        # lets have this FOIA do some things
        actstream.action.send(foia, verb='created')
        # lets also create an agency to act upon our FOIA
        agency = factories.AgencyFactory()
        actstream.action.send(agency, verb='rejected', action_object=foia)
        # lets also have the user follow somebody
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user, actor_only=False)
        # lets generate some actions on behalf of this other user
        actstream.action.send(other_user, verb='acted')
        actstream.action.send(agency, verb='sent an email', target=other_user)
        email = self.digest(self.user)
        logging.info(email.message())


class TestDailyTask(TestCase):
    """Tests the daily email notification task."""
    def setUp(self):
        # create a user to notify about an activity
        # right now special emails are limited to staff only
        self.staff_user = factories.UserFactory(is_staff=True)
        other_user = factories.UserFactory()
        actstream.actions.follow(self.staff_user, other_user)
        actstream.action.send(other_user, verb='acted')

    @mock.patch('muckrock.message.digests.DailyDigest.send')
    @mock.patch('muckrock.accounts.models.Profile.send_notifications')
    def test_daily_notification_task(self, mock_send, mock_profile_send):
        """Make sure the send method is called for the staff user."""
        tasks.daily_digest()
        mock_send.assert_called_once_with(self.staff_user)
        mock_profile_send.assert_called_once()


class TestWelcomeTask(TestCase):
    """Tests the welcome email notification sent to new users."""
    def setUp(self):
        self.user = factories.UserFactory()

    @mock.patch('muckrock.message.notifications.WelcomeNotification.send')
    def test_welcome_notification_task(self, mock_send):
        """Make sure the notification is actually sent!"""
        tasks.welcome(self.user)
        mock_send.assert_called_once()


class TestGiftTask(TestCase):
    """Tests the gift email notification sent to gift recipients."""
    def setUp(self):
        self.user = factories.UserFactory()
        self.sender = factories.UserFactory()
        self.gift = '4 requests'

    @mock.patch('muckrock.message.notifications.GiftNotification.send')
    def test_gift_notification_task(self, mock_send):
        """Make sure the notification is actually sent."""
        tasks.gift(self.user, self.sender, self.gift)
        mock_send.assert_called_once()


class TestEmailChangeTask(TestCase):
    """Tests the email change notification."""
    def setUp(self):
        self.user = factories.UserFactory()

    @mock.patch('muckrock.message.notifications.EmailChangeNotification.send')
    def test_email_change_task(self, mock_send):
        """Make sure the notification is actually sent."""
        tasks.email_change(self.user, 'old.email@email.com')
        mock_send.assert_called_once()


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
        mock_send.assert_called_once_with(self.user, mock_charge)

    @mock.patch('muckrock.message.receipts.RequestFeeReceipt.send')
    def test_request_fee_receipt(self, mock_send):
        """A receipt should be sent after request fee is paid."""
        # pylint: disable=no-member
        foia = factories.FOIARequestFactory()
        mock_charge.metadata['action'] = 'request-fee'
        mock_charge.metadata['foia'] = foia.pk
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_once_with(self.user, mock_charge)

    @mock.patch('muckrock.message.receipts.MultiRequestReceipt.send')
    def test_multirequest_receipt(self, mock_send):
        """A receipt should be sent after a multi-request is purchased."""
        mock_charge.metadata['action'] = 'request-multi'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_once_with(self.user, mock_charge)

    @mock.patch('muckrock.message.receipts.CrowdfundPaymentReceipt.send')
    def test_crowdfund_payment_receipt(self, mock_send):
        """A receipt should be sent after a crowdfund payment is made."""
        mock_charge.metadata['action'] = 'crowdfund-payment'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_once_with(self.user, mock_charge)

    @mock.patch('muckrock.message.receipts.GenericReceipt.send')
    def test_other_receipt(self, mock_send):
        """A generic receipt should be sent for any other charges."""
        mock_charge.metadata['action'] = 'unknown-charge'
        tasks.send_charge_receipt(mock_charge.id)
        mock_send.assert_called_once_with(self.user, mock_charge)

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
        customer_id = 'test-pro'
        profile = factories.ProfileFactory(customer_id=customer_id)
        mock_invoice.customer = customer_id
        tasks.send_invoice_receipt(mock_invoice)
        mock_send.assert_called_once_with(profile.user, mock_charge)

    @mock.patch('muckrock.message.receipts.OrgSubscriptionReceipt.send')
    def test_org_invoice_receipt(self, mock_send):
        """A receipt should be sent after an org subscription payment is made."""
        customer_id = 'test-org'
        owner = factories.UserFactory(profile__customer_id=customer_id)
        factories.OrganizationFactory(owner=owner)
        mock_invoice.customer = customer_id
        tasks.send_invoice_receipt(mock_invoice.id)
        mock_send.assert_called_once_with(owner, mock_charge)


@mock.patch('stripe.Invoice', MockInvoice)
class TestFailedPaymentTask(TestCase):
    """Tests the failed payment task."""
    # pylint:disable=no-member

    def setUp(self):
        mock_invoice.plan.id = 'pro'
        mock_invoice.attempt_count = 1
        self.profile = factories.ProfileFactory(customer_id=mock_invoice.customer)

    @mock.patch('muckrock.message.notifications.FailedPaymentNotification.send')
    def test_failed_invoice_charge(self, mock_send):
        """Make sure the send method is called for a failed payment notification"""
        tasks.failed_payment(mock_invoice.id)
        mock_send.assert_called_once_with(self.profile.user)
        self.profile.refresh_from_db()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')

    @mock.patch('muckrock.message.notifications.FailedPaymentNotification.send')
    @mock.patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_last_attempt_pro(self, mock_send, mock_cancel):
        """After the last attempt at payment, cancel the user's pro subscription"""
        self.profile.payment_failed = True
        self.profile.save()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')
        mock_invoice.attempt_count = 4
        tasks.failed_payment(mock_invoice.id)
        self.profile.refresh_from_db()
        mock_send.assert_called_once_with(self.profile.user)
        mock_cancel.assert_called_once()
        ok_(not self.profile.payment_failed, 'The payment failed flag should be lowered.')

    @mock.patch('muckrock.message.notifications.FailedPaymentNotification.send')
    @mock.patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_last_attempt_org(self, mock_send, mock_cancel):
        """After the last attempt at payment, cancel the user's org subscription"""
        self.profile.payment_failed = True
        self.profile.save()
        ok_(self.profile.payment_failed, 'The payment failed flag should be raised.')
        factories.OrganizationFactory(owner=self.profile.user)
        mock_invoice.attempt_count = 4
        mock_invoice.plan.id = 'org'
        tasks.failed_payment(mock_invoice.id)
        self.profile.refresh_from_db()
        mock_send.assert_called_once_with(self.profile.user)
        mock_cancel.assert_called_once()
        ok_(not self.profile.payment_failed, 'The payment failed flag should be lowered.')
