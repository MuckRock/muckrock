"""
Jurisdiction models for FOIA Coach API.
"""
from django.db import models


class ResourceProviderUpload(models.Model):
    """
    Tracks the upload status of a JurisdictionResource to a specific provider.

    This through model enables multi-provider support, allowing the same resource
    to be uploaded to multiple AI providers (OpenAI, Gemini, etc.) for comparison.
    """

    resource = models.ForeignKey(
        'JurisdictionResource',
        on_delete=models.CASCADE,
        related_name='provider_uploads',
        help_text='The resource being uploaded'
    )
    provider = models.CharField(
        max_length=20,
        choices=[
            ('openai', 'OpenAI'),
            ('gemini', 'Gemini'),
            ('mock', 'Mock (Testing)')
        ],
        help_text='RAG provider for this upload'
    )

    # Provider-specific IDs and metadata
    provider_file_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Provider-specific file/document ID'
    )
    provider_store_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Provider-specific store/vector store ID'
    )
    provider_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Provider-specific metadata'
    )

    # Status tracking
    index_status = models.CharField(
        max_length=20,
        choices=[
            ('not_uploaded', 'Not Uploaded'),
            ('pending', 'Pending Upload'),
            ('uploading', 'Uploading'),
            ('indexing', 'Indexing'),
            ('ready', 'Ready'),
            ('error', 'Error')
        ],
        default='pending',
        help_text='Upload and indexing status (defaults to pending to trigger automatic upload)'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if upload failed'
    )

    # Timestamps
    indexed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the resource was successfully indexed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'foia_coach_resourceproviderupload'
        unique_together = [('resource', 'provider')]
        ordering = ['provider']
        indexes = [
            models.Index(fields=['provider', 'index_status']),
            models.Index(fields=['resource', 'provider']),
        ]

    def __str__(self):
        return f"{self.resource.display_name} → {self.provider} ({self.index_status})"


class JurisdictionResource(models.Model):
    """
    Knowledge resource file associated with a jurisdiction.
    Jurisdiction data is fetched from MuckRock API, not stored locally.
    """

    # Store jurisdiction reference as simple fields (no FK)
    jurisdiction_id = models.IntegerField(
        help_text='ID from main MuckRock jurisdiction table'
    )
    jurisdiction_abbrev = models.CharField(
        max_length=5,
        help_text='State abbreviation (e.g., CO, GA, TN)'
    )

    file = models.FileField(
        upload_to='foia_coach/jurisdiction_resources/%Y/%m/',
        max_length=255,
        help_text='Text or Markdown file with state-specific FOIA knowledge'
    )
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Legacy Gemini-specific fields (deprecated - migrated to ResourceProviderUpload)
    gemini_file_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='DEPRECATED: Migrated to ResourceProviderUpload model'
    )
    gemini_display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='DEPRECATED: No longer used'
    )

    resource_type = models.CharField(
        max_length=50,
        choices=[
            ('law_guide', 'Law Guide'),
            ('request_tips', 'Request Tips'),
            ('exemptions', 'Exemptions Guide'),
            ('agency_info', 'Agency Information'),
            ('case_law', 'Case Law'),
            ('general', 'General Information')
        ],
        default='general'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'foia_coach_jurisdictionresource'
        ordering = ['jurisdiction_abbrev', 'order', 'display_name']
        indexes = [
            models.Index(fields=['jurisdiction_abbrev']),
            models.Index(fields=['jurisdiction_id']),
        ]

    def __str__(self):
        return f"{self.jurisdiction_abbrev} - {self.display_name}"

    @property
    def jurisdiction(self):
        """Fetch full jurisdiction data from MuckRock API"""
        from .services.muckrock_client import MuckRockAPIClient
        client = MuckRockAPIClient()
        return client.get_jurisdiction(self.jurisdiction_abbrev)

    def get_upload_status(self, provider):
        """
        Get upload status for a specific provider.

        Args:
            provider: Provider name ('openai', 'gemini', 'mock')

        Returns:
            ResourceProviderUpload instance or None if not found
        """
        try:
            return self.provider_uploads.get(provider=provider)
        except ResourceProviderUpload.DoesNotExist:
            return None

    def initiate_upload(self, provider):
        """
        Queue this resource for upload to a provider.

        Creates a ResourceProviderUpload record with status='pending',
        which triggers the upload signal.

        Args:
            provider: Provider name ('openai', 'gemini', 'mock')

        Returns:
            ResourceProviderUpload instance
        """
        upload, created = self.provider_uploads.get_or_create(
            provider=provider,
            defaults={'index_status': 'pending'}
        )
        if not created and upload.index_status in ['error', 'not_uploaded']:
            upload.index_status = 'pending'
            upload.save(update_fields=['index_status', 'updated_at'])
        return upload

    def get_upload_summary(self):
        """
        Get a summary of upload status across all providers.

        Returns:
            dict mapping provider names to their status
            Example: {'openai': 'ready', 'gemini': 'pending'}
        """
        return {
            upload.provider: upload.index_status
            for upload in self.provider_uploads.all()
        }
