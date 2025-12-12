"""
Tests for ResourceProviderUpload model and multi-provider functionality
"""
# Third Party
import pytest
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

# Local
from apps.jurisdiction import factories
from apps.jurisdiction.models import ResourceProviderUpload


class TestResourceProviderUploadModel(TestCase):
    """Tests for ResourceProviderUpload model"""

    def setUp(self):
        """Set up test fixtures"""
        self.resource = factories.JurisdictionResourceFactory(
            jurisdiction_id=1,
            jurisdiction_abbrev='CO',
            display_name='Colorado FOIA Guide'
        )

    def test_create_upload_record(self):
        """Test creating a ResourceProviderUpload record"""
        upload = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='pending'
        )

        assert upload.id is not None
        assert upload.resource == self.resource
        assert upload.provider == 'openai'
        assert upload.index_status == 'pending'
        assert upload.error_message == ''

    def test_unique_constraint(self):
        """Test that resource + provider combination is unique"""
        # Create first upload
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )

        # Try to create duplicate
        with pytest.raises(IntegrityError):
            ResourceProviderUpload.objects.create(
                resource=self.resource,
                provider='openai',
                index_status='pending'
            )

    def test_multiple_providers_same_resource(self):
        """Test that a resource can have uploads to multiple providers"""
        openai_upload = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )
        gemini_upload = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='gemini',
            index_status='pending'
        )

        assert self.resource.provider_uploads.count() == 2
        assert openai_upload.provider == 'openai'
        assert gemini_upload.provider == 'gemini'

    def test_upload_status_display(self):
        """Test __str__ method"""
        upload = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )

        expected = "Colorado FOIA Guide → openai (ready)"
        assert str(upload) == expected

    def test_cascade_delete(self):
        """Test that deleting a resource cascades to upload records"""
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='gemini',
            index_status='ready'
        )

        assert ResourceProviderUpload.objects.count() == 2

        # Delete the resource
        self.resource.delete()

        # Upload records should be deleted too
        assert ResourceProviderUpload.objects.count() == 0


class TestJurisdictionResourceHelperMethods(TestCase):
    """Tests for helper methods on JurisdictionResource"""

    def setUp(self):
        """Set up test fixtures"""
        self.resource = factories.JurisdictionResourceFactory(
            jurisdiction_abbrev='CO'
        )

    def test_get_upload_status_exists(self):
        """Test get_upload_status when upload record exists"""
        upload = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )

        result = self.resource.get_upload_status('openai')
        assert result == upload
        assert result.index_status == 'ready'

    def test_get_upload_status_not_exists(self):
        """Test get_upload_status when upload record doesn't exist"""
        result = self.resource.get_upload_status('openai')
        assert result is None

    def test_initiate_upload_new(self):
        """Test initiate_upload creates new upload record"""
        upload = self.resource.initiate_upload('openai')

        assert upload is not None
        assert upload.provider == 'openai'
        assert upload.index_status == 'pending'
        assert upload.resource == self.resource

    def test_initiate_upload_retry_error(self):
        """Test initiate_upload retries failed upload"""
        # Create an errored upload
        existing = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='error',
            error_message='Previous error'
        )

        # Initiate upload should reset to pending
        upload = self.resource.initiate_upload('openai')

        assert upload.id == existing.id
        assert upload.index_status == 'pending'

    def test_initiate_upload_skip_ready(self):
        """Test initiate_upload doesn't reset ready uploads"""
        # Create a ready upload
        existing = ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )

        # Initiate upload should return existing without changing status
        upload = self.resource.initiate_upload('openai')

        assert upload.id == existing.id
        assert upload.index_status == 'ready'

    def test_get_upload_summary_empty(self):
        """Test get_upload_summary with no uploads"""
        summary = self.resource.get_upload_summary()
        assert summary == {}

    def test_get_upload_summary_multiple_providers(self):
        """Test get_upload_summary with multiple provider uploads"""
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='openai',
            index_status='ready'
        )
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='gemini',
            index_status='pending'
        )
        ResourceProviderUpload.objects.create(
            resource=self.resource,
            provider='mock',
            index_status='error'
        )

        summary = self.resource.get_upload_summary()

        assert summary == {
            'openai': 'ready',
            'gemini': 'pending',
            'mock': 'error'
        }


class TestResourceProviderUploadFactory(TestCase):
    """Tests for ResourceProviderUploadFactory"""

    def test_factory_creates_valid_upload(self):
        """Test factory creates valid upload with all required fields"""
        upload = factories.ResourceProviderUploadFactory()

        assert upload.id is not None
        assert upload.resource is not None
        assert upload.provider in ['openai', 'gemini', 'mock']
        assert upload.provider_file_id.startswith(upload.provider)
        assert upload.provider_store_id.startswith(upload.provider)
        assert upload.index_status == 'pending'

    def test_factory_with_custom_provider(self):
        """Test factory with custom provider"""
        upload = factories.ResourceProviderUploadFactory(provider='openai')

        assert upload.provider == 'openai'
        assert 'openai' in upload.provider_file_id

    def test_factory_with_existing_resource(self):
        """Test factory can use existing resource"""
        resource = factories.JurisdictionResourceFactory()
        upload1 = factories.ResourceProviderUploadFactory(
            resource=resource,
            provider='openai'
        )
        upload2 = factories.ResourceProviderUploadFactory(
            resource=resource,
            provider='gemini'
        )

        assert upload1.resource == resource
        assert upload2.resource == resource
        assert resource.provider_uploads.count() == 2
