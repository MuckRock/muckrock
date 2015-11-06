"""
Tests the notification application.
"""

from django.test import TestCase

import actstream
import logging
import mock
import nose.tools

from muckrock import factories
from muckrock.notification.tasks import daily_notification
from muckrock.notification.messages import DailyNotification

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestDailyNotification(TestCase):
    """Tests the daily email notification object. It extends Django's built-in email classes."""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_init(self):
        """The email should create when given a User."""
        ok_(DailyNotification(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        # pylint:disable=no-self-use
        DailyNotification(None)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = DailyNotification(self.user)
        eq_(email.send(), 0)

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user)
        actstream.action.send(other_user, verb='acted')
        # generate the email, which should contain the generated action
        email = DailyNotification(self.user)
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
        email = DailyNotification(self.user)
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

    @mock.patch('muckrock.notification.messages.DailyNotification.send')
    @mock.patch('muckrock.accounts.models.Profile.send_notifications')
    def test_daily_notification_task(self, mock_send, mock_profile_send):
        """Make sure the send method is called for the staff user."""
        daily_notification()
        mock_send.assert_called_once_with(self.staff_user)
        mock_profile_send.assert_called_once()
