"""
Serilizers for the organization application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.organization.models import Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""

    # make this not read only, so it can be set on creation
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = Organization
        fields = (
            'name',
            'uuid',
            'private',
            'individual',
            'plan',
        )


class MembershipReadSerializer(serializers.ModelSerializer):
    """Serializer for reading Membership model"""

    user = serializers.StringRelatedField(source='user.profile.uuid')
    organization = serializers.StringRelatedField(source='organization.uuid')

    class Meta:
        model = Membership
        fields = (
            'user',
            'organization',
            'active',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Membership.objects.all(),
                fields=('user', 'organization'),
            )
        ]


class MembershipWriteSerializer(serializers.Serializer):
    """Serializer for writing Membership model"""
    # pylint: disable=abstract-method

    user = serializers.UUIDField()
    organization = serializers.UUIDField()

    def validate_user(self, value):
        """Ensure the user UUID exists"""
        if not Profile.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("User does not exist")
        return value

    def validate_organization(self, value):
        """Ensure the organization UUID exists"""
        if not Organization.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("Organization does not exist")
        return value

    def create(self, validated_data):
        """Create memberhsip based on UUID's"""
        user = User.objects.get(profile__uuid=self.initial_data['user'])
        organization = Organization.objects.get(
            uuid=self.initial_data['organization']
        )
        return Membership.objects.create(user=user, organization=organization)
