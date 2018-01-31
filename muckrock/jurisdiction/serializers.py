"""
Serilizers for the Jurisdiction application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.jurisdiction.models import ExampleAppeal, Exemption, Jurisdiction


class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisidction model"""
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.order_by(),
        style={'base_template': 'input.html'},
    )
    absolute_url = serializers.ReadOnlyField(source='get_absolute_url')
    average_response_time = serializers.ReadOnlyField()
    fee_rate = serializers.ReadOnlyField()
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = Jurisdiction
        fields = (
            'id',
            'name',
            'slug',
            'full_name',
            'abbrev',
            'level',
            'parent',
            'public_notes',
            'days',
            'requires_proxy',
            # computed fields
            'absolute_url',
            'average_response_time',
            'fee_rate',
            'success_rate',
        )


class ExampleAppealSerializer(serializers.ModelSerializer):
    """Serializer for ExampleAppeals, included in the Exemption serializer."""

    class Meta:
        model = ExampleAppeal
        fields = (
            'id',
            'language',
            'context',
        )


class ExemptionSerializer(serializers.ModelSerializer):
    """Serializer for Exemption model"""
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.order_by(),
        style={
            'base_template': 'input.html'
        }
    )
    example_appeals = ExampleAppealSerializer(many=True)
    absolute_url = serializers.ReadOnlyField(source='get_absolute_url')

    class Meta:
        model = Exemption
        fields = (
            'id',
            'name',
            'slug',
            'jurisdiction',
            'basis',
            'example_appeals',
            # computed fields
            'absolute_url',
        )
