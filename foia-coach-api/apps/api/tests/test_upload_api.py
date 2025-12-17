"""
Tests for resource upload API endpoint
"""
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.jurisdiction import factories
from apps.jurisdiction.models import JurisdictionResource, ResourceProviderUpload


class TestResourceUploadAPI(TestCase):
    """Tests for /api/v1/resources/upload/ endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.upload_url = '/api/v1/resources/upload/'

    def test_upload_pdf_success(self):
        """Test successful PDF upload"""
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile(
            "test_guide.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO',
            'provider': 'openai'
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['jurisdiction_abbrev'] == 'CO'
        assert response.data['display_name'] == 'test guide'
        assert 'upload_status' in response.data

        # Verify resource created
        resource = JurisdictionResource.objects.get(id=response.data['id'])
        assert resource.jurisdiction_abbrev == 'CO'

        # Verify provider upload initiated
        upload = resource.get_upload_status('openai')
        assert upload is not None
        assert upload.index_status == 'pending'

    def test_upload_missing_file(self):
        """Test upload without file fails"""
        response = self.client.post(self.upload_url, {
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data or 'error' in response.data

    def test_upload_non_pdf_fails(self):
        """Test upload with non-PDF file fails"""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b'plain text content',
            content_type="text/plain"
        )

        response = self.client.post(self.upload_url, {
            'file': txt_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_oversized_file_fails(self):
        """Test upload with file > 25MB fails"""
        # Create a 26MB fake file
        large_content = b'0' * (26 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': large_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_auto_generates_display_name(self):
        """Test display name auto-generation from filename"""
        pdf_file = SimpleUploadedFile(
            "TN_FOIA_Law_Guide_2024.pdf",
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 155,
            'jurisdiction_abbrev': 'TN'
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['display_name'] == 'TN FOIA Law Guide 2024'

    def test_upload_with_custom_metadata(self):
        """Test upload with custom display_name and description"""
        pdf_file = SimpleUploadedFile(
            "guide.pdf",
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO',
            'display_name': 'Custom Guide Name',
            'description': 'Custom description',
            'resource_type': 'law_guide'
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['display_name'] == 'Custom Guide Name'
        assert response.data['description'] == 'Custom description'
        assert response.data['resource_type'] == 'law_guide'

    def test_upload_auto_assigns_order(self):
        """Test order is auto-assigned based on existing resources"""
        # Create existing resources
        factories.JurisdictionResourceFactory.create_batch(
            3,
            jurisdiction_abbrev='CO',
            order=0
        )

        pdf_file = SimpleUploadedFile(
            "new.pdf",
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        # Order should be 1 (max existing order + 1)
        resource = JurisdictionResource.objects.get(id=response.data['id'])
        assert resource.order == 1

    def test_upload_filename_too_long_fails(self):
        """Test upload with filename exceeding 209 characters fails with helpful message"""
        # Create a filename that's 210 characters long (exceeds limit)
        long_filename = "a" * 206 + ".pdf"  # 210 chars total
        pdf_file = SimpleUploadedFile(
            long_filename,
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data
        error_message = str(response.data['file'][0])
        assert 'Filename is too long' in error_message
        assert '210 characters' in error_message
        assert 'Please rename the file' in error_message

    def test_upload_filename_at_max_length_succeeds(self):
        """Test upload with filename at exactly 209 characters succeeds"""
        # Create a filename that's exactly 209 characters long (at limit)
        filename = "a" * 205 + ".pdf"  # 209 chars total
        pdf_file = SimpleUploadedFile(
            filename,
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 1,
            'jurisdiction_abbrev': 'CO'
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_upload_long_descriptive_filename_fails_with_preview(self):
        """Test that error message includes filename preview for long filenames"""
        # Create a realistic long filename like the one that failed
        # This needs to be > 209 characters to trigger the error
        long_filename = (
            "op1999-090 if exit conference called by auditor to provide "
            "information to governing body violates Open Meetings Act and "
            "requires public notice for all attendees regardless of their "
            "official status or role in the government organization today.pdf"
        )
        # Verify it's actually too long (should be > 209)
        assert len(long_filename) > 209

        pdf_file = SimpleUploadedFile(
            long_filename,
            b'%PDF-1.4 fake',
            content_type="application/pdf"
        )

        response = self.client.post(self.upload_url, {
            'file': pdf_file,
            'jurisdiction_id': 155,
            'jurisdiction_abbrev': 'TN'
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data
        error_message = str(response.data['file'][0])
        # Should show first 50 chars of filename
        assert 'op1999-090 if exit conference called by auditor' in error_message
