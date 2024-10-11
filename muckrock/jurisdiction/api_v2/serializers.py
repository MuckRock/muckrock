""" Serializer for Jurisdictions """

from rest_framework import serializers
from muckrock.jurisdiction.models import Jurisdiction

#pylint: disable=too-few-public-methods
class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisdiction model"""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.order_by(), style={"base_template": "input.html"}
    )

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
        )
