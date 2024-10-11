"""
Serializers for the Agency application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

#pylint: disable=too-few-public-methods
class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""

    types = serializers.StringRelatedField(many=True)
    appeal_agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={"base_template": "input.html"}
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={"base_template": "input.html"}
    )
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(), style={"base_template": "input.html"}
    )

    class Meta:
        """Options for the Agency serializer"""
        model = Agency
        fields = (
            # describes agency
            "id",
            "name",
            "slug",
            "status",
            "exempt",
            "types",
            "requires_proxy",
            "jurisdiction",
            # connects to other agencies
            "parent",
            "appeal_agency",
        )
