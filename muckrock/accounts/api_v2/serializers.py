"""
Serializers for the accounts application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.accounts.models import Profile

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with relevant Profile fields."""

    full_name = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source='profile.full_name',
        style={"base_template": "input.html"},
        help_text="The full name of the user"
    )
    uuid = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source='profile.uuid',
        style={"base_template": "input.html"},
        help_text="The UUID of the user's profile"
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
