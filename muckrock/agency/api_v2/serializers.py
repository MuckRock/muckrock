"""
Serializers for the Agency application API
"""

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example Agency",
            value={
                "id": 1,
                "name": "Environmental Protection Agency",
                "slug": "environmental-protection-agency",
                "status": "approved",
                "exempt": False,
                "requires_proxy": False,
                "jurisdiction": 10,
                "types": ["Executive"],
                "parent": None,
                "appeal_agency": None,
            },
        )
    ]
)
# pylint: disable=too-few-public-methods
class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""

    types = serializers.StringRelatedField(many=True)
    appeal_agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the agency to which appeals are directed",
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the parent agency",
    )
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the jurisdiction this agency operates under",
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
