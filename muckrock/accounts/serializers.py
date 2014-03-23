"""
Serilizers for the accounts application API
"""

from django.contrib.auth.models import User

from rest_framework import serializers

from muckrock.accounts.models import Profile

# pylint: disable=R0903

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model"""

    class Meta:
        model = Profile
        exclude = ('user', 'follows_foia', 'follows_question', 'notifications')

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile = ProfileSerializer(source='profile_set')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser',
                  'last_login', 'date_joined', 'groups', 'profile')
