"""
Serializers for FOIA Coach API
"""
import os
from django.db import models
from rest_framework import serializers
from apps.jurisdiction.models import ExampleResponse, JurisdictionResource, NFOICPartner


class JurisdictionSerializer(serializers.Serializer):
    """
    Serializer for Jurisdiction data fetched from MuckRock API.
    Works with dictionary data, not Django models.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    abbrev = serializers.CharField()
    level = serializers.CharField()
    resource_count = serializers.SerializerMethodField()

    def get_resource_count(self, obj):
        """Count active resources for this jurisdiction"""
        # obj is a dictionary from MuckRock API with 'id' field
        jurisdiction_id = obj.get('id')
        if jurisdiction_id:
            return JurisdictionResource.objects.filter(
                jurisdiction_id=jurisdiction_id,
                is_active=True
            ).count()
        return 0


class JurisdictionResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for JurisdictionResource model.
    """
    jurisdiction_name = serializers.SerializerMethodField()
    file_url = serializers.FileField(source='file', read_only=True)
    upload_status = serializers.SerializerMethodField()

    class Meta:
        model = JurisdictionResource
        fields = [
            'id',
            'jurisdiction_id',
            'jurisdiction_abbrev',
            'jurisdiction_name',
            'display_name',
            'description',
            'resource_type',
            'is_active',
            'created_at',
            'updated_at',
            'file_url',
            'order',
            'upload_status',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'upload_status'
        ]

    def get_jurisdiction_name(self, obj):
        """Fetch jurisdiction name from MuckRock API"""
        jurisdiction = obj.jurisdiction
        if jurisdiction:
            return jurisdiction.get('name', '')
        return ''

    def get_upload_status(self, obj):
        """Get upload status summary across all providers"""
        return obj.get_upload_summary()


class JurisdictionResourceUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading jurisdiction resources.
    Handles file validation and auto-generation of metadata.
    """
    provider = serializers.ChoiceField(
        choices=['openai', 'gemini', 'mock'],
        default='openai',
        write_only=True,
        required=False
    )

    class Meta:
        model = JurisdictionResource
        fields = [
            'file',
            'jurisdiction_id',
            'jurisdiction_abbrev',
            'display_name',
            'description',
            'resource_type',
            'order',
            'provider'
        ]
        extra_kwargs = {
            'display_name': {'required': False},
            'description': {'required': False},
            'resource_type': {'required': False},
            'order': {'required': False}
        }

    def validate_file(self, value):
        """Validate uploaded file"""
        # Check extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext != '.pdf':
            raise serializers.ValidationError(
                "Only PDF files are allowed"
            )

        # Check size (25MB max)
        if value.size > 25 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size must not exceed 25MB"
            )

        # Check filename length
        # The file field has max_length=255, and the upload path is:
        # foia_coach/jurisdiction_resources/YYYY/MM/filename
        # Path prefix is ~46 chars, so max filename length is ~209 chars
        MAX_FILENAME_LENGTH = 209
        if len(value.name) > MAX_FILENAME_LENGTH:
            raise serializers.ValidationError(
                f"Filename is too long ({len(value.name)} characters). "
                f"Please rename the file to {MAX_FILENAME_LENGTH} characters or fewer and try again. "
                f"Current filename: {value.name[:50]}..."
            )

        return value

    def create(self, validated_data):
        """Create resource with auto-generated metadata"""
        # Remove provider from validated_data (not a model field)
        validated_data.pop('provider', None)

        # Auto-generate display_name if not provided
        if not validated_data.get('display_name'):
            filename = validated_data['file'].name
            name = os.path.splitext(filename)[0]
            # Clean up: replace underscores/hyphens with spaces
            name = name.replace('_', ' ').replace('-', ' ')
            validated_data['display_name'] = name

        # Auto-generate description if not provided
        if not validated_data.get('description'):
            validated_data['description'] = (
                "Resource uploaded via batch upload"
            )

        # Auto-assign order if not provided
        if validated_data.get('order') is None:
            # Get max order for this jurisdiction
            max_order = JurisdictionResource.objects.filter(
                jurisdiction_abbrev=validated_data['jurisdiction_abbrev']
            ).aggregate(models.Max('order'))['order__max']
            validated_data['order'] = (max_order or 0) + 1

        # Set defaults
        validated_data.setdefault('resource_type', 'general')
        validated_data.setdefault('is_active', True)

        return super().create(validated_data)


class ExampleResponseSerializer(serializers.ModelSerializer):
    """Serializer for ExampleResponse model."""
    scope = serializers.SerializerMethodField()

    class Meta:
        model = ExampleResponse
        fields = [
            'id',
            'title',
            'jurisdiction_abbrev',
            'scope',
            'user_question',
            'assistant_response',
            'is_active',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_scope(self, obj):
        return obj.jurisdiction_abbrev or "global"


class NFOICPartnerSerializer(serializers.ModelSerializer):
    """Serializer for NFOICPartner model."""

    class Meta:
        model = NFOICPartner
        fields = [
            'id',
            'jurisdiction_abbrev',
            'name',
            'website',
            'email',
            'phone',
            'description',
            'is_active',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class QueryRequestSerializer(serializers.Serializer):
    """
    Serializer for RAG query requests.
    """
    question = serializers.CharField(required=True, help_text="The FOIA question to ask")
    state = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional state abbreviation to filter context (e.g., 'CO', 'GA')"
    )
    context = serializers.JSONField(
        required=False,
        help_text="Optional additional context as JSON object"
    )
    provider = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional RAG provider to use (e.g., 'openai', 'gemini', 'mock'). Defaults to RAG_PROVIDER setting."
    )
    model = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional model to use (e.g., 'gemini-2.0-flash-live', 'gpt-4o'). Defaults to provider's default model."
    )
    system_prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Optional custom system instruction to override default FOIA Coach prompt"
    )


class CitationSerializer(serializers.Serializer):
    """
    Serializer for citation objects with inline positioning and resource metadata.
    """
    # Core citation fields
    source = serializers.CharField(
        help_text="Filename or source identifier"
    )
    file_id = serializers.CharField(
        required=False,
        help_text="Provider-specific file ID"
    )

    # Inline positioning fields
    text = serializers.CharField(
        required=False,
        help_text="Citation marker text (e.g., '[1]')"
    )
    start_index = serializers.IntegerField(
        required=False,
        help_text="Starting character index in the answer text"
    )
    end_index = serializers.IntegerField(
        required=False,
        help_text="Ending character index in the answer text"
    )
    index = serializers.IntegerField(
        required=False,
        help_text="Alternative index field for citation numbering"
    )

    # Quote/content fields
    quote = serializers.CharField(
        required=False,
        help_text="Quoted text from the source document"
    )
    content = serializers.CharField(
        required=False,
        help_text="Legacy content field for backward compatibility"
    )

    # Resource metadata (enriched from JurisdictionResource)
    display_name = serializers.CharField(
        required=False,
        help_text="Human-readable resource name"
    )
    jurisdiction_abbrev = serializers.CharField(
        required=False,
        help_text="State/jurisdiction abbreviation"
    )
    file_url = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="URL to the uploaded PDF file"
    )


class QueryResponseSerializer(serializers.Serializer):
    """
    Serializer for RAG query responses.
    """
    answer = serializers.CharField(help_text="The generated answer from the RAG provider")
    citations = CitationSerializer(
        many=True,
        help_text="List of source documents cited in the answer with inline positioning"
    )
    provider = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="RAG provider that generated the response"
    )
    model = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Model used to generate the response"
    )
    state = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="State context used for the query"
    )
