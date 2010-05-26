"""
Tests for site level functionality and helper functions for application tests
"""

from django.test.client import Client
from django.core.urlresolvers import reverse

import nose.tools

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

 # tests for base level pages
def test_views():
    """Test views"""

    client = Client()
    get_allowed(client, reverse('index'))
    get_allowed(client, reverse('sitemap'))
    get_allowed(client, '/search/')
