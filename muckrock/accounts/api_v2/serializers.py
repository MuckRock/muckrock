"""
Serializers for the accounts application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.jurisdiction.models import Jurisdiction


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with embedded Profile fields."""

    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        required=False,
    )
    full_name = serializers.CharField(source='profile.full_name', required=False)
    city = serializers.CharField(source='profile.city', required=False)
    state = serializers.CharField(source='profile.state', required=False)
    zip_code = serializers.CharField(source='profile.zip_code', required=False)
    public_email = serializers.EmailField(source='profile.public_email', required=False)
    location = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(),
        style={"base_template": "input.html"},
        required=False,
    )
    # pylint: disable=too-few-public-methods
    class Meta:
        """ Fields """
        model = User
        fields = (
            "username",
            "email",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "full_name",
            "city",
            "state",
            "zip_code",
            "public_email",
            "location",
        )
