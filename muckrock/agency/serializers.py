"""
Serilizers for the Agency application API
"""

from rest_framework import serializers

from muckrock.agency.models import Agency

# pylint: disable=R0903

class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""
    types = serializers.RelatedField(many=True)
    class Meta:
        model = Agency
        fields = ('id', 'name', 'slug', 'jurisdiction', 'types', 'public_notes', 'address',
                  'contact_salutation', 'contact_first_name', 'contact_last_name',
                  'contact_title', 'url', 'expires', 'phone', 'fax')

