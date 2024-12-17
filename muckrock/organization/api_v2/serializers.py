"""
Serializers for organizations
"""

# Django
from django.contrib.auth.models import User

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.organization.models import Entitlement, Organization


# pylint:disable = too-few-public-methods
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example Organization",
            value={
                "id": 161,
                "name": "Example Organization",
                "slug": "example-organization",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "individual": False,
                "entitlement": 1,
                "verified_journalist": False,
                "users": [1, 3],
            },
        )
    ]
)
class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model with relevant fields."""

    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        help_text="List of user IDs associated with the organization",
    )
    entitlement = serializers.PrimaryKeyRelatedField(
        queryset=Entitlement.objects.all(),
        help_text="ID of the entitlements associated with the organization",
    )

    class Meta:
        """Fields"""

        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "uuid",
            "individual",
            "entitlement",
            "verified_journalist",
            "users",
        ]
        extra_kwargs = {
            "id": {"help_text": "The numerical ID of the organization."},
            "name": {"help_text": "The name of the organization."},
            "slug": {"help_text": "The slug (URL identifier) for the organization."},
            "uuid": {"help_text": "The unique identifier for the organization."},
            "individual": {
                "help_text": "Indicates if the organization is individual or not."
            },
            "entitlement": {
                "help_text": ("ID of the entitlements associated with the organization")
            },
            "verified_journalist": {
                "help_text": (
                    "Indicates if the organization is verified as a journalist."
                )
            },
            "users": {"help_text": "List of users associated with the organization"},
        }
