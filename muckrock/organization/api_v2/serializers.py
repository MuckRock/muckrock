"""
Serializers for organizations
"""

# Third Party
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema_serializer,
)
from rest_framework import serializers


# MuckRock
from muckrock.organization.models import Organization, Entitlement
from muckrock.accounts.api_v2.serializers import UserSerializer

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example Organization",
            value={
                "name": "Example Organization",
                "slug": "example-organization",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "individual": False,
                "entitlement": 1,
                "verified_journalist": False,
                "users": [
                    {
                        "username": "jdoe",
                        "email": "jdoe@example.com",
                        "last_login": "2023-10-20T12:34:56Z",
                        "date_joined": "2023-01-01T00:00:00Z",
                        "full_name": "John Doe",
                        "uuid": "123e4567-e89b-12d3-a456-426614174001",
                    },
                    {
                        "username": "asmith",
                        "email": "asmith@example.com",
                        "last_login": "2023-10-21T12:34:56Z",
                        "date_joined": "2023-02-01T00:00:00Z",
                        "full_name": "Alice Smith",
                        "uuid": "123e4567-e89b-12d3-a456-426614174002",
                    }
                ]
            },
        )
    ]
)

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model with relevant fields."""

    users = UserSerializer(many=True, help_text="List of users associated with the organization")
    entitlement = serializers.PrimaryKeyRelatedField(
        queryset=Entitlement.objects.all(),
        help_text="ID of the entitlements associated with the organization"
    )

    class Meta:
        """Fields"""
        model = Organization
        fields = [
            'name',
            'slug',
            'uuid',
            'individual',
            'entitlement',
            'verified_journalist',
            'users'
        ]
