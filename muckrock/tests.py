"""
Tests for site level functionality and helper functions for application tests
"""

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase

from mock import Mock
import logging
import nose.tools

from muckrock.fields import EmailsListField

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

logging.disable(logging.CRITICAL)

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
    nose.tools.eq_(response.redirect_chain, [('https://testserver:80' + redirect, 302)])

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
    redirect = 'https://testserver:80/accounts/login/?next=' + url
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

