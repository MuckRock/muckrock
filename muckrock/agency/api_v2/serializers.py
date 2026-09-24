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
                "state": None,
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

    types = serializers.StringRelatedField(
        many=True,
        help_text="The types of the agency (e.g., Executive, Legislative, Police, etc).",
    )
    appeal_agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the agency to which appeals are directed",
        required=False,
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
    state = serializers.SerializerMethodField(
        help_text=(
            "Jurisdiction ID of the state this"
            " agency belongs to, or null for federal agencies"
        )
    )

    def get_state(self, obj) -> int | None:
        """The state jurisdiction for state and local agencies"""
        jurisdiction = obj.jurisdiction
        if jurisdiction.level == "s":
            return jurisdiction.pk
        if jurisdiction.level == "l":
            return jurisdiction.parent_id
        return None

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
            "state",
            # connects to other agencies
            "parent",
            "appeal_agency",
        )
        extra_kwargs = {
            "id": {"help_text": "The unique identifier for this agency."},
            "name": {"help_text": "The name of the agency."},
            "slug": {"help_text": "The slug (URL identifier) for the agency."},
            "status": {"help_text": ("The current status of the agency")},
            "exempt": {
                "help_text": (
                    "Indicates whether the agency is exempt from records laws "
                )
            },
            "requires_proxy": {
                "help_text": (
                    "Indicates whether the agency requires a proxy "
                    "because of in-state residency laws."
                )
            },
        }
