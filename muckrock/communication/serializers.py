"""
Serilizers for the Communication application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.communication.models import Address, EmailAddress, PhoneNumber


class EmailAddressSerializer(serializers.ModelSerializer):
    """Email Address Serializer"""

    class Meta:
        model = EmailAddress
        fields = ('email', 'name', 'status')


class PhoneNumberSerializer(serializers.ModelSerializer):
    """Phone Number Serializer"""

    class Meta:
        model = PhoneNumber
        fields = ('number', 'type', 'status')


class AddressSerializer(serializers.ModelSerializer):
    """Address Serializer"""

    class Meta:
        model = Address
        fields = (
            'street',
            'suite',
            'city',
            'state',
            'zip_code',
            'agency_override',
            'attn_override',
            'address',
        )
