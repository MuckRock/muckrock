"""
Tests the messages application tasks.
These will usually tell us if a message
object cannot be instantiated.
"""

# Django
from django.test import TestCase

# Third Party
import mock
import nose.tools
from dateutil.relativedelta import relativedelta

# MuckRock
from muckrock.core.factories import NotificationFactory, ProjectFactory, UserFactory
from muckrock.message import tasks
from muckrock.task.factories import FlaggedTaskFactory

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises


class TestDailyTask(TestCase):
    """Tests the daily email notification task."""

    def setUp(self):
        self.user = UserFactory()

    @mock.patch("muckrock.message.tasks.send_activity_digest.delay")
    def test_when_unread(self, mock_send):
        """The send method should be called when a user has unread notifications."""
        NotificationFactory(user=self.user)
        tasks.daily_digest()
        mock_send.assert_called_with(self.user.pk, "Daily Digest", "daily")

    @mock.patch("muckrock.message.tasks.send_activity_digest.delay")
    def test_when_no_unread(self, mock_send):
        """The send method should not be called when a user does not have unread notifications."""
        tasks.daily_digest()
        mock_send.assert_not_called()


class TestStaffTask(TestCase):
    """Tests the daily staff digest task."""

    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)

    @mock.patch("muckrock.message.digests.StaffDigest.send")
    def test_staff_digest_task(self, mock_send):
        """Make sure the send method is called with the staff user."""
        tasks.staff_digest()
        mock_send.assert_called_with()


@mock.patch("muckrock.message.email.TemplateEmail.send")
class TestNotificationTasks(TestCase):
    """Email notifications are sent to users upon key events."""

    def setUp(self):
        self.user = UserFactory()

    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def test_support(self, mock_send):
        """Notifies the user with a support response."""
        task = FlaggedTaskFactory()
        tasks.support(self.user.pk, "Hello", task.pk)
        mock_send.assert_called_with(fail_silently=False)

    def test_notify_contributor(self, mock_send):
        """Notifies a contributor that they were added to a project."""
        project = ProjectFactory()
        added_by = UserFactory()
        tasks.notify_project_contributor(self.user.pk, project.pk, added_by.pk)
        mock_send.assert_called_with(fail_silently=False)
