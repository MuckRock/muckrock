"""
Serializers for FOIA Coach API
"""
from rest_framework import serializers
from apps.jurisdiction.models import JurisdictionResource


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
            'index_status',
            'indexed_at',
            'is_active',
            'created_at',
            'updated_at',
            'file_url',
            'order',
        ]
        read_only_fields = ['index_status', 'indexed_at', 'created_at', 'updated_at']

    def get_jurisdiction_name(self, obj):
        """Fetch jurisdiction name from MuckRock API"""
        jurisdiction = obj.jurisdiction
        if jurisdiction:
            return jurisdiction.get('name', '')
        return ''


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
    model = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional Gemini model to use (e.g., 'gemini-2.0-flash-live', 'gemini-1.5-pro'). Defaults to GEMINI_MODEL setting."
    )


class QueryResponseSerializer(serializers.Serializer):
    """
    Serializer for RAG query responses.
    """
    answer = serializers.CharField(help_text="The generated answer from Gemini")
    citations = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of source documents cited in the answer"
    )
    state = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="State context used for the query"
    )
