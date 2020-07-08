"""
Tests accounts views
"""

# Django
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.test import RequestFactory, TestCase

# Third Party
from mock import patch
from nose.tools import eq_, ok_, raises

# MuckRock
from muckrock.accounts import views
from muckrock.core.factories import (
    AgencyFactory,
    NotificationFactory,
    QuestionFactory,
    UserFactory,
)
from muckrock.core.test_utils import (
    http_get_response,
    http_post_response,
    mock_middleware,
)
from muckrock.core.utils import new_action, notify
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory
from muckrock.foia.views import Detail as FOIARequestDetail
from muckrock.qanda.views import Detail as QuestionDetail


def http_get_post(url, view, data):
    """Performs both a GET and a POST on the same url and view."""
    get_response = http_get_response(url, view)
    post_response = http_post_response(url, view, data)
    return (get_response, post_response)


class TestAccountFunctional(TestCase):
    """Functional tests for account"""

    def setUp(self):
        self.user = UserFactory()

    def test_public_views(self):
        """Test public views while not logged in"""
        # give the user a composer so they have a public profile
        FOIAComposerFactory(user=self.user, status="submitted")
        response = http_get_response(reverse("acct-login"), login)
        eq_(response.status_code, 200)
        # account overview page
        response = http_get_response(reverse("accounts"), views.AccountsView.as_view())
        eq_(response.status_code, 302)
        # profile page
        request_factory = RequestFactory()
        request = request_factory.get(self.user.profile.get_absolute_url())
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = views.ProfileView.as_view()(request, username=self.user.username)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_private_profile(self):
        """Test public views while not logged in"""
        response = http_get_response(reverse("acct-login"), login)
        eq_(response.status_code, 200)
        # account overview page
        response = http_get_response(reverse("accounts"), views.AccountsView.as_view())
        eq_(response.status_code, 302)
        # profile page
        request_factory = RequestFactory()
        request = request_factory.get(self.user.profile.get_absolute_url())
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = views.ProfileView.as_view()(request, username=self.user.username)

    def test_unallowed_views(self):
        """Private URLs should redirect logged-out users to the log in page"""
        # my profile
        get, post = http_get_post(
            reverse("acct-my-profile"), login_required(views.ProfileView.as_view()), {}
        )
        eq_(
            get.status_code, 302, "My profile link reponds with 302 to logged out user."
        )
        eq_(post.status_code, 302, "POST to my profile link responds with 302.")
        # settings
        get, post = http_get_post(
            reverse("acct-settings"), views.ProfileSettings.as_view(), {}
        )
        eq_(get.status_code, 302, "GET /profile responds with 302 to logged out user.")
        eq_(
            post.status_code, 302, "POST /settings reponds with 302 to logged out user."
        )

    @patch("stripe.Customer.retrieve")
    def test_auth_views(self, mock_stripe):
        """Test private views while logged in"""
        # pylint: disable=unused-argument
        response = http_get_response(
            reverse("acct-my-profile"), views.ProfileView.as_view(), self.user
        )
        eq_(response.status_code, 302, "Logged in user may view their own profile.")
        response = http_get_response(
            reverse("acct-settings"), views.ProfileSettings.as_view(), self.user
        )
        eq_(response.status_code, 200, "Logged in user may view their own settings.")

    @patch("stripe.Customer.retrieve")
    def test_settings_view(self, mock_stripe):
        """Test the account settings view"""
        # pylint: disable=unused-argument
        profile = self.user.profile
        profile_data = {"action": "profile", "twitter": "allanlasser"}
        email_data = {"action": "email", "email_pref": "hourly"}
        settings_url = reverse("acct-settings")
        http_post_response(
            settings_url, views.ProfileSettings.as_view(), profile_data, self.user
        )
        http_post_response(
            settings_url, views.ProfileSettings.as_view(), email_data, self.user
        )
        self.user.refresh_from_db()
        profile.refresh_from_db()
        all_data = {}
        all_data.update(profile_data)
        all_data.update(email_data)
        all_data.pop("action")
        for key, val in all_data.items():
            eq_(val, getattr(profile, key))


class TestNotificationList(TestCase):
    """A user should be able to view lists of their notifications."""

    def setUp(self):
        self.user = UserFactory()
        self.unread_notification = NotificationFactory(user=self.user, read=False)
        self.read_notification = NotificationFactory(user=self.user, read=True)
        self.url = reverse("acct-notifications")
        self.view = views.NotificationList.as_view()

    def test_get(self):
        """The view should provide a list of notifications for the user."""
        response = http_get_response(self.url, self.view, self.user)
        eq_(response.status_code, 200, "The view should return OK.")
        object_list = response.context_data["object_list"]
        ok_(
            self.unread_notification in object_list,
            "The context should contain the unread notification.",
        )
        ok_(
            self.read_notification in object_list,
            "The context should contain the read notification.",
        )

    def test_unauthorized_get(self):
        """Logged out users trying to access the notifications
        view should be redirected to the login view."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 302, "The view should redirect.")
        ok_(
            reverse("acct-login") in response.url,
            "Logged out users should be redirected to the login view.",
        )

    def test_mark_all_read(self):
        """Users should be able to mark all their notifications as read."""
        data = {"action": "mark_all_read"}
        ok_(self.unread_notification.read is not True)
        http_post_response(self.url, self.view, data, self.user)
        self.unread_notification.refresh_from_db()
        ok_(
            self.unread_notification.read is True,
            "The unread notification should be marked as read.",
        )


class TestUnreadNotificationList(TestCase):
    """A user should be able to view lists of their unread notifications."""

    def setUp(self):
        self.user = UserFactory()
        self.unread_notification = NotificationFactory(user=self.user, read=False)
        self.read_notification = NotificationFactory(user=self.user, read=True)
        self.url = reverse("acct-notifications-unread")
        self.view = views.UnreadNotificationList.as_view()

    def test_get(self):
        """The view should provide a list of notifications for the user."""
        response = http_get_response(self.url, self.view, self.user)
        eq_(response.status_code, 200, "The view should return OK.")
        object_list = response.context_data["object_list"]
        ok_(
            self.unread_notification in object_list,
            "The context should contain the unread notification.",
        )
        ok_(
            self.read_notification not in object_list,
            "The context should not contain the read notification.",
        )

    def test_unauthorized_get(self):
        """Logged out users trying to access the notifications
        view should be redirected to the login view."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 302, "The view should redirect.")
        ok_(
            reverse("acct-login") in response.url,
            "Logged out users should be redirected to the login view.",
        )


class TestNotificationRead(TestCase):
    """Getting an object view should read its notifications for that user."""

    def setUp(self):
        self.user = UserFactory()
        UserFactory(username="MuckrockStaff")

    def test_get_foia(self):
        """Try getting the detail page for a FOIA Request with an unread notification."""
        agency = AgencyFactory()
        foia = FOIARequestFactory(agency=agency)
        view = FOIARequestDetail.as_view()
        # Create a notification for the request
        action = new_action(agency, "completed", target=foia)
        notification = notify(self.user, action)[0]
        ok_(not notification.read, "The notification should be unread.")
        # Try getting the view as the user
        response = http_get_response(
            foia.get_absolute_url(),
            view,
            self.user,
            idx=foia.pk,
            slug=foia.slug,
            jidx=foia.jurisdiction.pk,
            jurisdiction=foia.jurisdiction.slug,
        )
        eq_(response.status_code, 200, "The view should response 200 OK.")
        # Check that the notification has been read.
        notification.refresh_from_db()
        ok_(notification.read, "The notification should be marked as read.")

    def test_get_question(self):
        """Try getting the detail page for a Question with an unread notification."""
        question = QuestionFactory()
        view = QuestionDetail.as_view()
        # Create a notification for the question
        action = new_action(UserFactory(), "answered", target=question)
        notification = notify(self.user, action)[0]
        ok_(not notification.read, "The notification should be unread.")
        # Try getting the view as the user
        response = http_get_response(
            question.get_absolute_url(),
            view,
            self.user,
            pk=question.pk,
            slug=question.slug,
        )
        eq_(response.status_code, 200, "The view should respond 200 OK.")
        # Check that the notification has been read.
        notification.refresh_from_db()
        ok_(notification.read, "The notification should be marked as read.")
