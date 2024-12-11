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
        extra_kwargs = {
            "id": {"help_text": "The unique identifier for this agency."},
            "name": {"help_text": "The name of the agency."},
            "slug": {"help_text": "The slug (URL identifier) for the agency."},
            "status": {
                "help_text": (
                    "The current status of the agency (e.g., approved, pending, rejected)."
                )
            },
            "exempt": {
                "help_text": (
                    "Indicates whether the agency is exempt from records laws "
                    "(True/False)."
                )
            },
            "types": {
                "help_text": "The types of the agency (e.g., Executive, Legislative, Police, etc)."
            },
            "requires_proxy": {
                "help_text": (
                    "Indicates whether the agency requires a proxy "
                    "because of in-state residency laws (True/False)."
                )
            },
            "jurisdiction": {
                "help_text": "The ID of the jurisdiction this agency operates under."
            },
            "parent": {"help_text": "The ID of the parent agency, if applicable."},
            "appeal_agency": {
                "help_text": "The ID of the agency to which appeals are directed, if applicable."
            },
        }
