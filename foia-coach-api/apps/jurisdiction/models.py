"""
Jurisdiction models for FOIA Coach API.
"""
from django.db import models


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
        help_text='Text or Markdown file with state-specific FOIA knowledge'
    )
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Gemini integration metadata
    gemini_file_id = models.CharField(max_length=255, blank=True, null=True)
    gemini_display_name = models.CharField(max_length=255, blank=True, null=True)
    indexed_at = models.DateTimeField(blank=True, null=True)
    index_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Upload'),
            ('uploading', 'Uploading'),
            ('indexing', 'Indexing'),
            ('ready', 'Ready'),
            ('error', 'Error')
        ],
        default='pending'
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
