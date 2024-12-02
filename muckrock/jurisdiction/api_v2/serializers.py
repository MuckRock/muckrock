""" Serializer for Jurisdictions """

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.jurisdiction.models import Jurisdiction


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "State Jurisdiction Example",
            value={
                "id": 1,
                "name": "California",
                "slug": "california",
                "abbrev": "CA",
                "level": "s",
                "parent": 3,
            },
            description="Example of a state jurisdiction under the USA.",
        ),
        OpenApiExample(
            "Local Jurisdiction Example",
            value={
                "id": 2,
                "name": "Los Angeles",
                "slug": "los-angeles",
                "abbrev": "",
                "level": "l",
                "parent": 1,
            },
            description="Example of a local jurisdiction under California.",
        ),
        OpenApiExample(
            "Federal Jurisdiction Example",
            value={
                "id": 3,
                "name": "United States of America",
                "slug": "united-states-of-america",
                "abbrev": "USA",
                "level": "f",
                "parent": None,
            },
            description="Example of a federal jurisdiction.",
        ),
    ]
)
# pylint: disable=too-few-public-methods
class JurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for Jurisdiction model"""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.order_by(),
        style={"base_template": "input.html"},
        help_text=(
            "Parent jurisdiction. This defines the hierarchy between jurisdictions, "
            "where a jurisdiction can have a federal or state parent. "
            "Local jurisdictions cannot be parents."
        )
    )

    class Meta:
        """Fields in Jurisdiction object"""

        model = Jurisdiction
        fields = (
            "id",
            "name",
            "slug",
            "abbrev",
            "level",
            "parent",
        )
