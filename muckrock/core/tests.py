"""
Tests for site level functionality and helper functions for application tests
"""

# Django
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

# Standard Library
import hashlib
import logging

# Third Party
import mock
import pytest
from actstream.models import Action
from mock import ANY, Mock, patch

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.core.context_processors import banner
from muckrock.core.factories import (
    AgencyFactory,
    AnswerFactory,
    ArticleFactory,
    QuestionFactory,
    UserFactory,
)
from muckrock.core.fields import EmailsListField
from muckrock.core.forms import NewsletterSignupForm
from muckrock.core.models import HomePage
from muckrock.core.templatetags import tags
from muckrock.core.test_utils import http_get_response, http_post_response
from muckrock.core.utils import new_action, notify, parse_header
from muckrock.core.views import NewsletterSignupView
from muckrock.crowdsource.factories import CrowdsourceResponseFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.factories import (
    FlaggedTaskFactory,
    NewAgencyTaskFactory,
    OrphanTaskFactory,
    ResponseTaskFactory,
    SnailMailTaskFactory,
)

logging.disable(logging.CRITICAL)

kwargs = {"wsgi.url_scheme": "https"}


# helper functions for view testing
def get_allowed(client, url, redirect=None):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, follow=True, **kwargs)
    assert response.status_code == 200

    if redirect:
        assert response.redirect_chain == [("https://testserver:80" + redirect, 302)]

    return response


def post_allowed(client, url, data, redirect):
    """Test an allowed post with the given data and redirect location"""
    response = client.post(url, data, follow=True, **kwargs)
    assert response.status_code == 200
    assert response.redirect_chain == [(redirect, 302)]

    return response


def post_allowed_bad(client, url, templates, data=None):
    """Test an allowed post with bad data"""
    if data is None:
        data = {"bad": "data"}
    response = client.post(url, data, **kwargs)
    assert response.status_code == 200
    # make sure first 3 match (4th one might be form.html, not important
    assert [t.name for t in response.templates][:3] == templates + ["base.html"]


def get_post_unallowed(client, url):
    """Test an unauthenticated get and post on a url that is allowed
    to be viewed only by authenticated users"""
    redirect = "/accounts/login/?next=" + url
    response = client.get(url, **kwargs)
    assert response.status_code == 302
    assert response["Location"] == redirect


def get_404(client, url):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, **kwargs)
    assert response.status_code == 404

    return response


class TestFunctional(TestCase):
    """Functional tests for top level"""

    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def setUp(self):
        AgencyFactory()
        ArticleFactory()
        CrowdsourceResponseFactory()
        FOIARequestFactory()
        FlaggedTaskFactory()
        NewAgencyTaskFactory()
        OrphanTaskFactory()
        QuestionFactory()
        ResponseTaskFactory()
        SnailMailTaskFactory()
        UserFactory()

    # tests for base level views
    def test_views(self):
        """Test views"""
        # we have no question fixtures
        # should move all fixtures to factories

        AnswerFactory()
        Site.objects.create(domain="www.muckrock.com")

        get_allowed(self.client, reverse("index"))
        get_allowed(self.client, "/sitemap.xml")
        get_allowed(self.client, "/sitemap-News.xml")
        get_allowed(self.client, "/sitemap-Jurisdiction.xml")
        get_allowed(self.client, "/sitemap-Agency.xml")
        get_allowed(self.client, "/sitemap-Question.xml")
        get_allowed(self.client, "/sitemap-FOIA.xml")
        get_allowed(self.client, "/news-sitemaps/index.xml")
        get_allowed(self.client, "/news-sitemaps/articles.xml")
        get_allowed(self.client, "/search/")

    def test_api_views(self):
        """Test API views"""
        user = UserFactory(username="super", is_staff=True)
        self.client.force_login(user)
        api_objs = [
            "agency",
            "communication",
            "crowdsource-response",
            "exemption",
            "flaggedtask",
            "foia",
            "jurisdiction",
            "newagencytask",
            "news",
            "orphantask",
            "photos",
            "responsetask",
            "snailmailtask",
            "statistics",
            "task",
            "user",
        ]
        for obj in api_objs:
            print(obj)
            get_allowed(self.client, reverse("api-%s-list" % obj))


class TestUnit(TestCase):
    """Unit tests for top level"""

    def test_emails_list_field(self):
        """Test email list field"""
        model_instance = Mock()
        field = EmailsListField(max_length=255)

        with pytest.raises(ValidationError):
            field.clean("a@example.com,not.an.email", model_instance)

        with pytest.raises(ValidationError):
            field.clean("", model_instance)

        field.clean("a@example.com,an.email@foo.net", model_instance)


class TestNewsletterSignupView(TestCase):
    """By submitting an email, users can subscribe to our MailChimp newsletter list."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = NewsletterSignupView.as_view()
        self.url = reverse("newsletter")

    def test_get_view(self):
        """GET is not allowed - POST only"""
        response = http_get_response(self.url, self.view)
        assert response.status_code == 405

    @patch("muckrock.core.views.mailchimp_subscribe")
    def test_post_view(self, mock_subscribe):
        """Posting an email to the list should add that email to our MailChimp list."""
        form = NewsletterSignupForm(
            {"email": "test@muckrock.com", "list": settings.MAILCHIMP_LIST_DEFAULT}
        )
        assert form.is_valid(), "The form should validate."
        response = http_post_response(self.url, self.view, form.data)
        mock_subscribe.assert_called_with(
            ANY,
            form.data["email"],
            form.data["list"],
            source="Newsletter Sign Up Form",
            url="{}/newsletter-post/".format(settings.MUCKROCK_URL),
        )
        assert (
            response.status_code == 302
        ), "Should redirect upon successful submission."

    @patch("muckrock.core.views.mailchimp_subscribe")
    def test_post_other_list(self, mock_subscribe):
        """Posting to a list other than the default should optionally subscribe
        to the default."""
        form = NewsletterSignupForm(
            {"email": "test@muckrock.com", "default": True, "list": "other"}
        )
        assert form.is_valid(), "The form should validate."
        mock_subscribe.return_value = False
        response = http_post_response(self.url, self.view, form.data)
        mock_subscribe.assert_any_call(
            ANY,
            form.data["email"],
            form.data["list"],
            source="Newsletter Sign Up Form",
            url="{}/newsletter-post/".format(settings.MUCKROCK_URL),
        )
        mock_subscribe.assert_any_call(
            ANY,
            form.data["email"],
            settings.MAILCHIMP_LIST_DEFAULT,
            suppress_msg=True,
            source="Newsletter Sign Up Form",
            url="{}/newsletter-post/".format(settings.MUCKROCK_URL),
        )
        assert (
            response.status_code == 302
        ), "Should redirect upon successful submission."


class TestNewAction(TestCase):
    """The new action function will create a new action and return it."""

    def test_basic(self):
        """An action only needs an actor and a verb."""
        actor = UserFactory()
        verb = "acted"
        action = new_action(actor, verb)
        assert isinstance(action, Action), "An Action should be returned."
        assert action.actor == actor
        assert action.verb == verb


class TestNotify(TestCase):
    """The notify function will notify one or many users about an action."""

    def setUp(self):
        self.action = new_action(UserFactory(), "acted")

    def test_single_user(self):
        """Notify a single user about an action."""
        user = UserFactory()
        notifications = notify(user, self.action)
        assert isinstance(notifications, list), "A list should be returned."
        assert isinstance(
            notifications[0], Notification
        ), "The list should contain notification objects."

    def test_many_users(self):
        """Notify many users about an action."""
        users = [UserFactory(), UserFactory(), UserFactory()]
        notifications = notify(users, self.action)
        assert len(notifications) == len(
            users
        ), "There should be a notification for every user in the list."
        for user in users:
            notification_for_user = any(
                notification.user == user for notification in notifications
            )
            assert notification_for_user, "Each user in the list should be notified."


class TestTemplatetagsFunctional(TestCase):
    """Functional tests for templatetags"""

    def test_active(self):
        """Test the active template tag"""
        mock_request = Mock()
        mock_request.user = "adam"
        mock_request.path = "/test1/adam/"

        assert tags.active(mock_request, "/test1/{{user}}/") == "current-tab"
        assert tags.active(mock_request, "/test2/{{user}}/") == ""

    def test_company_title(self):
        """Test the company_title template tag"""

        assert tags.company_title("one\ntwo\nthree") == "one, et al"
        assert tags.company_title("company") == "company"


def test_parse_header():
    """Test the parse header util function"""

    assert parse_header("application/json") == ("application/json", {})
    assert parse_header('application/json; charset="utf8"') == (
        "application/json",
        {"charset": "utf8"},
    )
    assert parse_header('application/json; charset="utf8"; a="b"') == (
        "application/json",
        {"charset": "utf8", "a": "b"},
    )


class BannerContextProcessorTest(TestCase):
    """Test the banner context processor"""

    def setUp(self):
        self.factory = RequestFactory()
        self.homepage = None

    def test_banner_with_message(self):
        """Test banner context processor with a banner message"""
        homepage = HomePage.load()
        homepage.banner_message = "This is a test banner message"
        homepage.save()

        banner_hash = hashlib.md5(homepage.banner_message.encode("utf-8")).hexdigest()

        request = self.factory.get("/")
        request.session = {}

        context = banner(request)

        assert context["banner_message"] == "This is a test banner message"
        assert context["show_banner"] is True
        assert context["banner_message_hash"] == banner_hash

    def test_banner_without_message(self):
        """Test banner context processor without a banner message"""
        homepage = HomePage.load()
        homepage.banner_message = ""
        homepage.save()

        request = self.factory.get("/")
        request.session = {}

        context = banner(request)

        assert context["banner_message"] == ""
        assert context["show_banner"] is False
        assert context["banner_message_hash"] == ""

    def test_banner_dismissed_in_session(self):
        """Test banner context processor with dismissed banner in session"""
        homepage = HomePage.load()
        homepage.banner_message = "This is a test banner message"
        homepage.save()

        banner_hash = hashlib.md5(homepage.banner_message.encode("utf-8")).hexdigest()

        request = self.factory.get("/")
        request.session = {"dismissed_banners": [banner_hash]}

        context = banner(request)

        assert context["banner_message"] == "This is a test banner message"
        assert context["show_banner"] is False
        assert context["banner_message_hash"] == banner_hash


class DismissBannerViewTest(TestCase):
    """Test the dismiss_banner view"""

    def test_dismiss_banner_success(self):
        """Test successfully dismissing a banner"""
        client = Client()
        response = client.post(
            reverse("dismiss-banner"),
            data={"banner_hash": "abc123"},
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True

    def test_dismiss_banner_stores_in_session(self):
        """Test that dismissing a banner stores hash in session"""
        client = Client()
        response = client.post(
            reverse("dismiss-banner"),
            data={"banner_hash": "abc123"},
        )

        assert response.status_code == 200
        session = client.session
        assert "dismissed_banners" in session
        assert "abc123" in session["dismissed_banners"]

    def test_dismiss_banner_multiple_hashes(self):
        """Test dismissing multiple banners accumulates hashes"""
        client = Client()

        # Dismiss first banner
        client.post(reverse("dismiss-banner"), data={"banner_hash": "hash1"})
        # Dismiss second banner
        client.post(reverse("dismiss-banner"), data={"banner_hash": "hash2"})

        session = client.session
        assert "hash1" in session["dismissed_banners"]
        assert "hash2" in session["dismissed_banners"]
        assert len(session["dismissed_banners"]) == 2

    def test_dismiss_banner_duplicate_hash(self):
        """Test dismissing same banner twice doesn't duplicate"""
        client = Client()

        # Dismiss same banner twice
        client.post(reverse("dismiss-banner"), data={"banner_hash": "hash1"})
        client.post(reverse("dismiss-banner"), data={"banner_hash": "hash1"})

        session = client.session
        assert session["dismissed_banners"].count("hash1") == 1

    def test_dismiss_banner_no_hash(self):
        """Test dismissing without banner_hash returns error"""
        client = Client()
        response = client.post(reverse("dismiss-banner"), data={})

        assert response.status_code == 400
        json_data = response.json()
        assert json_data["success"] is False
        assert "No banner_hash provided" in json_data["error"]

    def test_dismiss_banner_get_method(self):
        """Test that GET method is not allowed"""
        client = Client()
        response = client.get(reverse("dismiss-banner"))

        assert response.status_code == 405
        json_data = response.json()
        assert json_data["success"] is False
        assert "Method not allowed" in json_data["error"]
