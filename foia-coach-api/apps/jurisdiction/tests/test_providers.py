"""
Tests for RAG provider system with MockProvider.
"""
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.jurisdiction import factories
from apps.jurisdiction.models import JurisdictionResource
from apps.jurisdiction.services.providers import (
    RAGProviderFactory,
    MockProvider,
    ProviderConfigError
)
from apps.jurisdiction.services.providers.helpers import get_provider, clear_provider_cache


class TestMockProvider(TestCase):
    """Tests for MockProvider - ensures no real API calls in tests"""

    def setUp(self):
        """Set up test fixtures"""
        # Disconnect signals to prevent automatic uploads during tests
        from django.db.models.signals import post_save
        from apps.jurisdiction.signals import upload_resource_to_provider
        post_save.disconnect(upload_resource_to_provider, sender=JurisdictionResource)

        # Clear provider cache
        clear_provider_cache()

        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_document.txt",
            b"Test content for public records guidance",
            content_type="text/plain"
        )

    def tearDown(self):
        """Clean up after tests"""
        # Reconnect signals
        from django.db.models.signals import post_save
        from apps.jurisdiction.signals import upload_resource_to_provider
        post_save.connect(upload_resource_to_provider, sender=JurisdictionResource)

    def test_mock_provider_registered(self):
        """Test that MockProvider is registered"""
        providers = RAGProviderFactory.list_providers()
        self.assertIn('mock', providers)

    def test_get_mock_provider(self):
        """Test getting MockProvider instance"""
        provider = get_provider('mock')
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.PROVIDER_NAME, 'mock')

    def test_mock_provider_no_api_calls(self):
        """Test that MockProvider never makes real API calls"""
        provider = get_provider('mock')

        # These should all work without any network calls
        store_id = provider.create_store('TestStore')
        self.assertIsNotNone(store_id)
        self.assertTrue(store_id.startswith('mock-store-'))

        # Get or create should work
        store_id2 = provider.get_or_create_store('TestStore')
        self.assertEqual(store_id, store_id2)  # Should return existing store

    def test_mock_provider_upload_resource(self):
        """Test uploading a resource with MockProvider"""
        provider = get_provider('mock')

        # Create a test resource
        resource = factories.JurisdictionResourceFactory(
            jurisdiction_id=1,
            jurisdiction_abbrev='CO',
            file=self.test_file,
            display_name='Test Resource',
            provider='mock',
            index_status='pending'
        )

        # Upload should work without API calls
        result = provider.upload_resource(resource)

        self.assertIn('file_id', result)
        self.assertIn('store_id', result)
        self.assertIn('metadata', result)
        self.assertTrue(result['file_id'].startswith('mock-file-'))

        # Resource should be updated
        resource.refresh_from_db()
        self.assertEqual(resource.index_status, 'ready')

    def test_mock_provider_remove_resource(self):
        """Test removing a resource with MockProvider"""
        provider = get_provider('mock')

        # Create a resource with provider_file_id
        resource = factories.JurisdictionResourceFactory(
            jurisdiction_id=1,
            jurisdiction_abbrev='CO',
            provider='mock',
            provider_file_id='mock-file-12345'
        )

        # Remove should work without errors
        provider.remove_resource(resource)  # Should not raise

    def test_mock_provider_query(self):
        """Test querying with MockProvider"""
        provider = get_provider('mock')

        result = provider.query(
            question="What is the FOIA deadline in Colorado?",
            state="CO"
        )

        self.assertIn('answer', result)
        self.assertIn('citations', result)
        self.assertIn('provider', result)
        self.assertIn('model', result)
        self.assertEqual(result['provider'], 'mock')
        self.assertEqual(result['state'], 'CO')

        # Answer should be a string
        self.assertIsInstance(result['answer'], str)
        self.assertGreater(len(result['answer']), 0)

        # Should have citations
        self.assertIsInstance(result['citations'], list)
        self.assertGreater(len(result['citations']), 0)

    def test_mock_provider_query_stream(self):
        """Test streaming query with MockProvider"""
        provider = get_provider('mock')

        chunks = list(provider.query_stream(
            question="What are FOIA fees?",
            state="GA"
        ))

        # Should have chunks, citations, and done
        chunk_types = [c['type'] for c in chunks]
        self.assertIn('chunk', chunk_types)
        self.assertIn('citations', chunk_types)
        self.assertIn('done', chunk_types)

        # Verify chunks have text
        text_chunks = [c for c in chunks if c['type'] == 'chunk']
        self.assertGreater(len(text_chunks), 0)
        self.assertIsInstance(text_chunks[0]['text'], str)

    def test_mock_provider_configurable_failure(self):
        """Test that MockProvider can be configured to fail for testing"""
        provider = get_provider('mock', use_cache=False)
        provider.configure_failure(should_fail=True, message="Test failure")

        # Operations should fail with configured message
        with self.assertRaises(ProviderConfigError) as cm:
            provider.create_store('TestStore')

        self.assertEqual(str(cm.exception), "Test failure")

    def test_mock_provider_reset(self):
        """Test resetting MockProvider state"""
        provider = get_provider('mock')

        # Create some state
        store_id = provider.create_store('TestStore')
        self.assertEqual(len(provider._stores), 1)

        # Reset
        provider.reset()
        self.assertEqual(len(provider._stores), 0)
        self.assertEqual(len(provider._files), 0)

    def test_test_settings_prevent_api_calls(self):
        """Test that test settings prevent real API calls"""
        from django.conf import settings

        # Real API calls should be disabled (critical safety measure)
        self.assertFalse(settings.OPENAI_REAL_API_ENABLED)
        self.assertFalse(settings.GEMINI_REAL_API_ENABLED)

        # Note: RAG_PROVIDER may be 'mock' or 'openai' depending on environment
        # but REAL_API_ENABLED flags ensure no actual API calls are made

    def test_no_accidental_api_calls_in_tests(self):
        """
        Test that ensures no real API calls can be made in test environment.

        This is a critical safety test to prevent accidental API usage and costs.
        """
        from django.conf import settings

        # Verify API call flags are disabled
        self.assertFalse(settings.OPENAI_REAL_API_ENABLED)
        self.assertFalse(settings.GEMINI_REAL_API_ENABLED)

        # Verify MockProvider works correctly (regardless of default provider)
        mock_provider = get_provider('mock')
        self.assertIsInstance(mock_provider, MockProvider)
        self.assertEqual(mock_provider.PROVIDER_NAME, 'mock')

        # Verify mock provider never makes real API calls
        result = mock_provider.query("Test question")
        self.assertIn('answer', result)
        self.assertEqual(result['provider'], 'mock')


class TestProviderFactory(TestCase):
    """Tests for RAGProviderFactory"""

    def setUp(self):
        """Set up test fixtures"""
        clear_provider_cache()

    def test_list_providers(self):
        """Test listing all registered providers"""
        providers = RAGProviderFactory.list_providers()
        self.assertIn('openai', providers)
        self.assertIn('gemini', providers)
        self.assertIn('mock', providers)

    def test_get_provider_by_name(self):
        """Test getting provider by name"""
        mock_provider = RAGProviderFactory.get_provider('mock')
        self.assertIsInstance(mock_provider, MockProvider)

    def test_get_provider_default(self):
        """Test getting default provider from settings"""
        from django.conf import settings

        # Should return provider based on RAG_PROVIDER setting
        provider = RAGProviderFactory.get_provider()
        self.assertEqual(provider.PROVIDER_NAME, settings.RAG_PROVIDER)

        # Verify real API calls are disabled
        self.assertFalse(settings.OPENAI_REAL_API_ENABLED)
        self.assertFalse(settings.GEMINI_REAL_API_ENABLED)

    def test_get_provider_invalid_name(self):
        """Test that invalid provider name raises error"""
        with self.assertRaises(ProviderConfigError):
            RAGProviderFactory.get_provider('invalid-provider')


class TestProviderHelpers(TestCase):
    """Tests for provider helper functions"""

    def setUp(self):
        """Set up test fixtures"""
        clear_provider_cache()

    def test_get_provider_with_cache(self):
        """Test that provider caching works"""
        provider1 = get_provider('mock', use_cache=True)
        provider2 = get_provider('mock', use_cache=True)

        # Should return same instance
        self.assertIs(provider1, provider2)

    def test_get_provider_without_cache(self):
        """Test getting provider without caching"""
        provider1 = get_provider('mock', use_cache=False)
        provider2 = get_provider('mock', use_cache=False)

        # Should return different instances
        self.assertIsNot(provider1, provider2)

    def test_clear_provider_cache(self):
        """Test clearing provider cache"""
        provider1 = get_provider('mock', use_cache=True)
        clear_provider_cache()
        provider2 = get_provider('mock', use_cache=True)

        # After clearing cache, should get new instance
        self.assertIsNot(provider1, provider2)
