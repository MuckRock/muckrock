"""
Tests for site level functionality and helper functions for application tests
"""

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from mock import Mock, patch
import logging
import nose.tools

from muckrock.fields import EmailsListField
from muckrock.forms import NewsletterSignupForm
from muckrock.utils import mock_middleware
from muckrock.views import NewsletterSignupView

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

logging.disable(logging.CRITICAL)

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
nottest = nose.tools.nottest

kwargs = {"wsgi.url_scheme": "https"}

# helper functions for view testing
def get_allowed(client, url, redirect=None):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, follow=True, **kwargs)
    nose.tools.eq_(response.status_code, 200)

    if redirect:
        nose.tools.eq_(response.redirect_chain, [('https://testserver:80' + redirect, 302)])

    return response

def post_allowed(client, url, data, redirect):
    """Test an allowed post with the given data and redirect location"""
    response = client.post(url, data, follow=True, **kwargs)
    nose.tools.eq_(response.status_code, 200)
    nose.tools.eq_(response.redirect_chain, [(redirect, 302)])

    return response

def post_allowed_bad(client, url, templates, data=None):
    """Test an allowed post with bad data"""
    if data is None:
        data = {'bad': 'data'}
    response = client.post(url, data, **kwargs)
    nose.tools.eq_(response.status_code, 200)
    # make sure first 3 match (4th one might be form.html, not important
    nose.tools.eq_([t.name for t in response.templates][:3], templates + ['base.html'])

def get_post_unallowed(client, url):
    """Test an unauthenticated get and post on a url that is allowed
    to be viewed only by authenticated users"""
    redirect = '/accounts/login/?next=' + url
    response = client.get(url, **kwargs)
    nose.tools.eq_(response.status_code, 302)
    nose.tools.eq_(response['Location'], redirect)

def get_404(client, url):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, **kwargs)
    nose.tools.eq_(response.status_code, 404)

    return response


class TestFunctional(TestCase):
    """Functional tests for top level"""
    fixtures = [
            'holidays.json',
            'jurisdictions.json',
            'agency_types.json',
            'test_agencies.json',
            'test_users.json',
            'test_profiles.json',
            'test_foiarequests.json',
            'test_foiacommunications.json',
            'test_news.json',
            ]

    # tests for base level views
    def test_views(self):
        """Test views"""

        get_allowed(self.client, reverse('index'))
        get_allowed(self.client, '/sitemap.xml')
        get_allowed(self.client, '/search/')

    def test_api_views(self):
        """Test API views"""
        self.client.login(username='super', password='abc')
        api_objs = ['jurisdiction', 'agency', 'foia', 'question', 'statistics',
                'communication', 'user', 'news', 'task', 'orphantask',
                'snailmailtask', 'rejectedemailtask', 'staleagencytask',
                'flaggedtask', 'newagencytask', 'responsetask']
        for obj in api_objs:
            get_allowed(self.client, reverse('api-%s-list' % obj))


class TestUnit(TestCase):
    """Unit tests for top level"""

    def test_emails_list_field(self):
        """Test email list field"""
        model_instance = Mock()
        field = EmailsListField(max_length=255)

        with nose.tools.assert_raises(ValidationError):
            field.clean('a@example.com,not.an.email', model_instance)

        with nose.tools.assert_raises(ValidationError):
            field.clean('', model_instance)

        field.clean('a@example.com,an.email@foo.net', model_instance)

class TestNewsletterSignupView(TestCase):
    """By submitting an email, users can subscribe to our MailChimp newsletter list."""
    def setUp(self):
        self.factory = RequestFactory()
        self.view = NewsletterSignupView.as_view()
        self.url = reverse('newsletter')

    def test_get_view(self):
        """Visiting the page should present a signup form."""
        request = self.factory.get(self.url)
        request.user = AnonymousUser()
        request = mock_middleware(request)
        response = self.view(request)
        eq_(response.status_code, 200)

    @patch('muckrock.views.NewsletterSignupView.subscribe')
    def test_post_view(self, mock_subscribe):
        """Posting an email to the list should add that email to our MailChimp list."""
        form = NewsletterSignupForm({
            'email': 'test@muckrock.com',
            'list': settings.MAILCHIMP_LIST_DEFAULT
        })
        ok_(form.is_valid(), 'The form should validate.')
        request = self.factory.post(self.url, form.data)
        request.user = AnonymousUser()
        request = mock_middleware(request)
        response = self.view(request)
        mock_subscribe.assert_called_with(form.data['email'], form.data['list'])
        eq_(response.status_code, 302, 'Should redirect upon successful submission.')

    @nottest
    def test_subscribe(self):
        """Tests the method for subscribing an email to a MailChimp list.
        This test should be disabled under normal conditions because it
        is using an external API call."""
        _email = 'test@muckrock.com'
        _list = settings.MAILCHIMP_LIST_DEFAULT
        response = NewsletterSignupView().subscribe(_email, _list)
        eq_(response.status_code, 200)
