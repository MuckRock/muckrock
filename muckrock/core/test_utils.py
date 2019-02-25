"""
Utilities for testing MuckRock applications
"""

# Django
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

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


def mock_squarelet(mock_requests):
    """Set up proper mock for squarelet"""
    mock_requests.post(
        settings.SQUARELET_URL + '/openid/token',
        json={'access_token': 'bacon',
              'expires_in': '60'},
    )

    def json_cb(request, context):
        """Call back to generate json response for mock request"""
        data = parse_qs(request.body)
        return {
            'id': unicode(uuid.uuid4()),
            'username': re.sub(r'[^\w\-.]', '', data['username'][0]),
            'name': data['name'][0],
            'email': data['email'][0],
        }

    mock_requests.post(
        settings.SQUARELET_URL + '/api/users/',
        json=json_cb,
    )
