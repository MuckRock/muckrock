"""
Serializers for the Crowdsource application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.crowdsource.models import CrowdsourceResponse, CrowdsourceValue


class CrowdsourceValueSerializer(serializers.ModelSerializer):
    """Serializer for the Crowdsource Value model"""

    field = serializers.StringRelatedField(source='field.label')

    class Meta:
        model = CrowdsourceValue
        exclude = ('id', 'response')


class CrowdsourceResponseSerializer(serializers.ModelSerializer):
    """Serializer for the Crowdsource Response model"""

    values = CrowdsourceValueSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(source='user.get_full_name')
    data = serializers.StringRelatedField(source='data.url')
    datetime = serializers.DateTimeField(format='%m/%d/%Y %I:%M %p')

    class Meta:
        model = CrowdsourceResponse
