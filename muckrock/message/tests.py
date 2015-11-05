"""
Tests the messages application.
"""

from django.test import TestCase

import actstream
import logging
import mock
import nose.tools

from muckrock import factories
from muckrock.message import tasks, notifications

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestDailyNotification(TestCase):
    """Tests the daily email notification object. It extends Django's built-in email classes."""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_init(self):
        """The email should create when given a User."""
        ok_(notifications.DailyNotification(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        # pylint:disable=no-self-use
        notifications.DailyNotification(None)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = notifications.DailyNotification(self.user)
        eq_(email.send(), 0)

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user)
        actstream.action.send(other_user, verb='acted')
        # generate the email, which should contain the generated action
        email = notifications.DailyNotification(self.user)
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
        email = notifications.DailyNotification(self.user)
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

    @mock.patch('muckrock.message.notifications.DailyNotification.send')
    @mock.patch('muckrock.accounts.models.Profile.send_notifications')
    def test_daily_notification_task(self, mock_send, mock_profile_send):
        """Make sure the send method is called for the staff user."""
        tasks.daily_notification()
        mock_send.assert_called_once_with(self.staff_user)
        mock_profile_send.assert_called_once()

class TestFailedPaymentTask(TestCase):
    """Tests the failed payment task."""
    def setUp(self):
        customer_id = 'test-customer'
        self.invoice = {
            'attempt_count': 1,
            'customer': customer_id
        }
        self.profile = factories.ProfileFactory(customer_id=customer_id)

    @mock.patch('muckrock.message.notifications.FailedPaymentNotification.send')
    def test_send_failed_payment_notification(self, mock_send):
        """Make sure the send method is called for a failed payment notification"""
        tasks.failed_payment(self.invoice)
        mock_send.assert_called_once_with(self.profile.user)

    @mock.patch('muckrock.message.notifications.FailedPaymentNotification.send')
    @mock.patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_last_attempt(self, mock_send, mock_cancel):
        """After the last attempt at payment, cancel the user's pro subscription"""
        self.invoice['attempt_count'] = 4
        tasks.failed_payment(self.invoice)
        mock_send.assert_called_once_with(self.profile.user)
        mock_cancel.assert_called_once()


class TestSendReceiptTask(TestCase):
    """Tests the send receipt task."""
    def setUp(self):
        self.user = factories.UserFactory()
        self.charge = {
            'metadata': {
                'email': self.user.email
            },
            'id': 'test-charge',
            'amount': 100,
            'created': 1446680016,
            'source': {
                'last4': '1234',
            }
        }

    @mock.patch('muckrock.message.receipts.RequestPurchaseReceipt.send')
    def testRequestPurchaseReceipt(self, mock_send):
        """A receipt should be sent after request bundle is purchased."""
        self.charge['metadata']['action'] = 'request-payment'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.RequestFeeReceipt.send')
    def testRequestFeeReceipt(self, mock_send):
        """A receipt should be sent after request fee is paid."""
        self.charge['metadata']['action'] = 'request-fee'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.MultiRequestReceipt.send')
    def testMultiRequestReceipt(self, mock_send):
        """A receipt should be sent after a multi-request is purchased."""
        self.charge['metadata']['action'] = 'request-multi'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.CrowdfundPaymentReceipt.send')
    def testCrowdfundPaymentReceipt(self, mock_send):
        """A receipt should be sent after a crowdfund payment is made."""
        self.charge['metadata']['action'] = 'crowdfund-payment'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.ProSubscriptionReceipt.send')
    def testProSubscriptionReceipt(self, mock_send):
        """A receipt should be sent after a pro subscription payment is made."""
        self.charge['metadata']['action'] = 'pro-subscription'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.OrgSubscriptionReceipt.send')
    def testOrgSubscriptionReceipt(self, mock_send):
        """A receipt should be sent after an org subscription payment is made."""
        self.charge['metadata']['action'] = 'org-subscription'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)

    @mock.patch('muckrock.message.receipts.GenericReceipt.send')
    def testOtherReceipt(self, mock_send):
        """A generic receipt should be sent for any other charges."""
        self.charge['metadata']['action'] = 'unknown-charge'
        tasks.send_receipt(self.charge)
        mock_send.assert_called_once_with(self.user)
