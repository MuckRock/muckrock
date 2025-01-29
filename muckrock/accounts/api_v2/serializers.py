"""
Serializers for the accounts application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.organization.models import Organization

# pylint:disable = too-few-public-methods


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example User",
            value={
                "id": 1,
                "username": "jdoe",
                "email": "jdoe@example.com",
                "last_login": "2023-10-20T12:34:56Z",
                "date_joined": "2023-01-01T00:00:00Z",
                "full_name": "John Doe",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
            },
        )
    ]
)
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with relevant Profile fields."""

    full_name = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source="profile.full_name",
        style={"base_template": "input.html"},
        help_text="The full name of the user",
    )
    uuid = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source="profile.uuid",
        style={"base_template": "input.html"},
        help_text="The UUID of the user's profile",
    )
    organizations = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        many=True,
        required=False,
        help_text="The IDs of the organizations the user belongs to",
    )

    organizations = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        many=True,
        required=False,
        help_text="The IDs of the organizations the user belongs to",
    )

    class Meta:
        """Fields"""

        model = User
        fields = (
            "id",
            "username",
            "email",
            "last_login",
            "date_joined",
            "full_name",
            "uuid",
            "organizations",
        )
        extra_kwargs = {
            "id": {"help_text": "The unique identifier for the user"},
            "username": {"help_text": "The unique username of the user."},
            "email": {"help_text": "The email address of the user."},
            "last_login": {"help_text": "The last time the user logged in."},
            "date_joined": {"help_text": "The date and time when the user joined."},
            "full_name": {"help_text": "The full name of the user."},
            "uuid": {
                "help_text": "The unique identifier (UUID) of the user's profile."
            },
        }
