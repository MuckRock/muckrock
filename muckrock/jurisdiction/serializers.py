"""
Serilizers for the Jurisdiction application API
"""

from rest_framework import serializers

from muckrock.jurisdiction.models import Jurisdiction

# pylint: disable=R0903

class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisidction model"""
    class Meta:
        model = Jurisdiction
        fields = ('id', 'name', 'slug', 'full_name', 'abbrev', 'level', 'parent', 'public_notes')
