""" Serializer for Jurisdictions """

from django.conf import settings
from rest_framework import serializers
from muckrock.jurisdiction.models import Jurisdiction

class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisdiction model"""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.order_by(), style={"base_template": "input.html"}
    )
    absolute_url = serializers.SerializerMethodField()
    average_response_time = serializers.ReadOnlyField()
    fee_rate = serializers.ReadOnlyField()
    success_rate = serializers.ReadOnlyField()

    class Meta:
        """ Fields in Jurisdiction object """
        model = Jurisdiction
        fields = (
            "id",
            "name",
            "slug",
            "abbrev",
            "level",
            "parent",
            "public_notes",
            # computed fields
            "absolute_url",
            "average_response_time",
            "fee_rate",
            "success_rate",
        )

    def get_absolute_url(self, obj): # pylint: disable=R0201
        """Prepend the domain name to the URL"""
        return f"{settings.MUCKROCK_URL}{obj.get_absolute_url()}"
