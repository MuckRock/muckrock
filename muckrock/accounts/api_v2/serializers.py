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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example User",
            value={
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

    class Meta:
        """Fields"""

        model = User
        fields = (
            "username",
            "email",
            "last_login",
            "date_joined",
            "full_name",
            "uuid",
        )
