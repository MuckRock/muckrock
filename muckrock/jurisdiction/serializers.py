"""
Serilizers for the Jurisdiction application API
"""

from rest_framework import serializers

from muckrock.jurisdiction.models import Jurisdiction

# pylint: disable=too-few-public-methods

class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisidction model"""
    parent = serializers.PrimaryKeyRelatedField(
            queryset=Jurisdiction.objects.all(),
            style={'base_template': 'input.html'})
    class Meta:
        model = Jurisdiction
        fields = ('id', 'name', 'slug', 'full_name', 'abbrev', 'level', 'parent', 'public_notes',
                  'days')
