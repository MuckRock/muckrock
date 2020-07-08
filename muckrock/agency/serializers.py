"""
Serilizers for the Agency application API
"""

# Django
from django.conf import settings

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.agency.models import Agency, AgencyAddress, AgencyEmail, AgencyPhone
from muckrock.communication.serializers import (
    AddressSerializer,
    EmailAddressSerializer,
    PhoneNumberSerializer,
)
from muckrock.jurisdiction.models import Jurisdiction


class AgencyAddressSerializer(serializers.ModelSerializer):
    """Serializer for AgencyAddress model"""

    address = AddressSerializer(read_only=True)

    class Meta:
        model = AgencyAddress
        fields = ("address", "request_type")


class AgencyEmailSerializer(serializers.ModelSerializer):
    """Serializer for AgencyEmail model"""

    email = EmailAddressSerializer(read_only=True)

    class Meta:
        model = AgencyEmail
        fields = ("email", "request_type", "email_type")


class AgencyPhoneSerializer(serializers.ModelSerializer):
    """Serializer for AgencyPhone model"""

    phone = PhoneNumberSerializer(read_only=True)

    class Meta:
        model = AgencyPhone
        fields = ("phone", "request_type")


class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""

    types = serializers.StringRelatedField(many=True)
    appeal_agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={"base_template": "input.html"}
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={"base_template": "input.html"}
    )
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(), style={"base_template": "input.html"}
    )
    absolute_url = serializers.SerializerMethodField()
    average_response_time = serializers.ReadOnlyField(source="average_response_time_")
    fee_rate = serializers.ReadOnlyField(source="fee_rate_")
    success_rate = serializers.ReadOnlyField(source="success_rate_")

    # contact fields
    has_portal = serializers.SerializerMethodField()
    has_email = serializers.SerializerMethodField()
    has_fax = serializers.SerializerMethodField()
    has_address = serializers.SerializerMethodField()
    addresses = AgencyAddressSerializer(
        many=True, read_only=True, source="agencyaddress_set"
    )
    emails = AgencyEmailSerializer(many=True, read_only=True, source="agencyemail_set")
    phones = AgencyPhoneSerializer(many=True, read_only=True, source="agencyphone_set")

    # request counts
    number_requests = serializers.ReadOnlyField()
    number_requests_completed = serializers.ReadOnlyField()
    number_requests_rejected = serializers.ReadOnlyField()
    number_requests_no_docs = serializers.ReadOnlyField()
    number_requests_ack = serializers.ReadOnlyField()
    number_requests_resp = serializers.ReadOnlyField()
    number_requests_fix = serializers.ReadOnlyField()
    number_requests_appeal = serializers.ReadOnlyField()
    number_requests_pay = serializers.ReadOnlyField()
    number_requests_partial = serializers.ReadOnlyField()
    number_requests_lawsuit = serializers.ReadOnlyField()
    number_requests_withdrawn = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        """After initializing the serializer,
        check that the current user has permission
        to view agency email data."""
        # pylint: disable=super-on-old-class
        super(AgencySerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request", None)
        if not (
            request is not None
            and request.user.is_authenticated
            and request.user.profile.is_advanced()
        ):
            # remove contact info fields for non advanced users
            self.fields.pop("addresses", None)
            self.fields.pop("emails", None)
            self.fields.pop("phones", None)

    def get_has_portal(self, obj):
        """Does this have a portal?"""
        return obj.portal_id is not None

    def get_has_email(self, obj):
        """Does this have a primary email address?"""
        # primary_emails attribute comes from prefetching
        return bool(obj.primary_emails)

    def get_has_fax(self, obj):
        """Does this have a primary fax number?"""
        # primary_faxes attribute comes from prefetching
        return bool(obj.primary_faxes)

    def get_has_address(self, obj):
        """Does this have a primary snail mail address?"""
        # primary_addresses attribute comes from prefetching
        return bool(obj.primary_addresses)

    def get_absolute_url(self, obj):
        """Prepend the domain name to the URL"""
        return "{}{}".format(settings.MUCKROCK_URL, obj.get_absolute_url())

    class Meta:
        model = Agency
        fields = (
            # describes agency
            "id",
            "name",
            "slug",
            "status",
            "exempt",
            "types",
            "requires_proxy",
            "jurisdiction",
            # contact info
            "website",
            "twitter",
            "twitter_handles",
            "addresses",
            "emails",
            "phones",
            # connects to other agencies
            "parent",
            "appeal_agency",
            # describes agency foia process
            "url",
            "foia_logs",
            "foia_guide",
            # misc
            "public_notes",
            # computed fields
            "absolute_url",
            "average_response_time",
            "fee_rate",
            "success_rate",
            "has_portal",
            "has_email",
            "has_fax",
            "has_address",
            "number_requests",
            "number_requests_completed",
            "number_requests_rejected",
            "number_requests_no_docs",
            "number_requests_ack",
            "number_requests_resp",
            "number_requests_fix",
            "number_requests_appeal",
            "number_requests_pay",
            "number_requests_partial",
            "number_requests_lawsuit",
            "number_requests_withdrawn",
        )
