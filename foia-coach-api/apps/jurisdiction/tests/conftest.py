"""
Pytest configuration for jurisdiction app tests
"""
# Third Party
import pytest
from django.db.models.signals import post_save, post_delete
from django.test import override_settings


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests"""
    pass


@pytest.fixture(autouse=True)
def disable_real_gemini_api_calls():
    """
    Disable real Gemini API calls for all tests.
    This is a critical safety measure to prevent tests from consuming API quota.
    """
    with override_settings(GEMINI_REAL_API_ENABLED=False):
        yield


@pytest.fixture(autouse=True)
def disconnect_gemini_signals():
    """
    Disconnect signal handlers that trigger Gemini uploads.
    Prevents automatic API calls when test models are created.
    """
    from apps.jurisdiction.models import JurisdictionResource
    from apps.jurisdiction.signals import (
        upload_resource_to_gemini,
        remove_resource_from_gemini
    )

    # Disconnect signals
    post_save.disconnect(upload_resource_to_gemini, sender=JurisdictionResource)
    post_delete.disconnect(remove_resource_from_gemini, sender=JurisdictionResource)

    yield

    # Reconnect signals after test
    post_save.connect(upload_resource_to_gemini, sender=JurisdictionResource)
    post_delete.connect(remove_resource_from_gemini, sender=JurisdictionResource)


@pytest.fixture
def gemini_service_with_real_api_enabled(settings):
    """
    Fixture for tests that explicitly want to test with API enabled flag.
    Use this sparingly and only with mocked API clients.
    """
    settings.GEMINI_REAL_API_ENABLED = True
    yield
    settings.GEMINI_REAL_API_ENABLED = False


@pytest.fixture(autouse=True)
def reset_gemini_request_tracking():
    """Reset Gemini API request tracking between tests"""
    from apps.jurisdiction.services.gemini_service import GeminiFileSearchService

    GeminiFileSearchService.reset_request_tracking()
    yield
    GeminiFileSearchService.reset_request_tracking()
