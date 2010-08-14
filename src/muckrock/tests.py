"""
Tests for site level functionality and helper functions for application tests
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

import nose.tools

from utils import try_or_none

# allow methods that could be functions and too many public methods in tests
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

 # helper functions for view testing
def get_allowed(client, url, templates=None, context=None):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url)
    nose.tools.eq_(response.status_code, 200)
    # make sure first 3 match (4th one might be form.html, not important
    if templates:
        nose.tools.eq_([t.name for t in response.template][:3], templates + ['base.html'])

    if context:
        for key, value in context.iteritems():
            nose.tools.eq_(response.context[key], value)

    return response

def post_allowed(client, url, data, redirect):
    """Test an allowed post with the given data and redirect location"""
    response = client.post(url, data)
    nose.tools.eq_(response.status_code, 302)
    nose.tools.eq_(response['Location'], redirect)

    return response

def post_allowed_bad(client, url, templates):
    """Test an allowed post with bad data"""
    response = client.post(url, {'bad': 'data'})
    nose.tools.eq_(response.status_code, 200)
    # make sure first 3 match (4th one might be form.html, not important
    nose.tools.eq_([t.name for t in response.template][:3], templates + ['base.html'])

def get_post_unallowed(client, url):
    """Test an unauthenticated get and post on a url that is allowed
    to be viewed only by authenticated users"""
    redirect = 'http://testserver/accounts/login/?next=' + url
    response = client.get(url)
    nose.tools.eq_(response.status_code, 302)
    nose.tools.eq_(response['Location'], redirect)

def get_404(client, url):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url)
    nose.tools.eq_(response.status_code, 404)

    return response


class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_foiarequests.json', 'test_news.json']

    # test utils
    def test_try_or_none(self):
        """Test the try_or_none util function"""
        nose.tools.eq_(try_or_none(ZeroDivisionError, lambda x: 10 / x, 5), 2)
        nose.tools.eq_(try_or_none(ZeroDivisionError, lambda x: 10 / x, 0), None)

    # tests for base level views
    def test_views(self):
        """Test views"""

        get_allowed(self.client, reverse('index'))
        get_allowed(self.client, reverse('sitemap'))
        get_allowed(self.client, '/search/')
