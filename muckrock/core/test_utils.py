"""
Utilities for testing MuckRock applications
"""

# Django
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils.text import slugify

# Standard Library
import re
import uuid
from urlparse import parse_qs

# Third Party
from mock import MagicMock


def mock_middleware(request):
    """Mocks the request with messages and session middleware"""
    setattr(request, 'session', MagicMock())
    setattr(request, '_messages', MagicMock())
    setattr(request, '_dont_enforce_csrf_checks', True)
    return request


def http_get_response(url, view, user=AnonymousUser(), **kwargs):
    """Handles making GET requests, returns the response."""
    request_factory = RequestFactory()
    request = request_factory.get(url, **kwargs)
    request = mock_middleware(request)
    request.user = user
    response = view(request, **kwargs)
    return response


def http_post_response(url, view, data, user=AnonymousUser(), **kwargs):
    """Handles making POST requests, returns the response."""
    request_factory = RequestFactory()
    request = request_factory.post(url, data, **kwargs)
    request = mock_middleware(request)
    request.user = user
    response = view(request, **kwargs)
    return response


def mock_squarelet(mock_requests, requests_json=None):
    """Set up proper mock for squarelet"""
    mock_requests.post(
        settings.SQUARELET_URL + '/openid/token',
        json={'access_token': 'bacon',
              'expires_in': '60'},
    )

    def users_cb(request, context):
        """Call back to generate json response for user creation"""
        data = parse_qs(request.body)
        username = re.sub(r'[^\w\-.]', '', data['preferred_username'][0])
        uuid_ = unicode(uuid.uuid4())
        return {
            'uuid':
                uuid_,
            'preferred_username':
                username,
            'name':
                data['name'][0],
            'email':
                data['email'][0],
            'email_failed':
                False,
            'email_verified':
                False,
            'is_agency':
                False,
            'organizations': [{
                'uuid': uuid_,
                'name': username,
                'slug': slugify(username),
                'update_on': None,
                'max_users': 1,
                'entitlements': [],
                'individual': True,
                'admin': True,
            }]
        }

    def requests_cb(request, context):
        """Call back to generate json response for make requests"""
        data = parse_qs(request.body)
        if 'amount' in data:
            return {
                'regular': data['amount'][0],
                'monthly': 0,
            }
        else:
            return "OK"

    mock_requests.post(
        settings.SQUARELET_URL + '/api/users/',
        json=users_cb,
    )

    if requests_json is None:
        requests_json = requests_cb
    mock_requests.post(
        re.compile(
            r'{}/api/organizations/[a-f0-9-]+/requests/'.format(
                settings.SQUARELET_URL
            )
        ),
        json=requests_json,
    )

    mock_requests.get(
        re.compile(
            r'{}/api/organizations/[a-f0-9-]+/'.format(settings.SQUARELET_URL)
        ),
        json={'number_requests': 5,
              'monthly_requests': 0},
    )
