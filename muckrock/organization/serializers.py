"""
Serilizers for the organization application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.organization.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""

    class Meta:
        model = Organization
        fields = (
            'name',
            'uuid',
            'private',
            'individual',
            'plan',
        )
