"""
Utilities for testing MuckRock applications
"""

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from mock import MagicMock

def mock_middleware(request):
    """Mocks the request with messages and session middleware"""
    setattr(request, 'session', MagicMock())
    setattr(request, '_messages', MagicMock())
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
