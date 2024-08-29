"""
Serilizers for V2 of the FOIA API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema_serializer,
)
from rest_framework import serializers

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.organization.models import Organization


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example 1",
            value={
                "id": 1,
                "title": "Meeting Minutes",
                "slug": "meeting-minutes",
                "status": "processed",
                "agency": 2,
                "embargo": False,
                "permanent_embargo": False,
                "user": 3,
                "edit_collaborators": [4, 5],
                "read_collaborators": [],
                "datetime_submitted": "2018-05-20T07:08:48.911320-04:00",
                "datetime_updated": "2019-02-18T05:00:01.355367-05:00",
                "datetime_done": None,
                "tracking_id": "ABC123-456",
                "price": "0.00",
            },
        )
    ]
)
class FOIARequestSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Request model"""

    user = serializers.PrimaryKeyRelatedField(
        source="composer.user",
        queryset=User.objects.all(),
        style={"base_template": "input.html"},
        help_text="The user ID of the user who filed this request",
        required=False,
    )
    datetime_submitted = serializers.DateTimeField(
        read_only=True,
        source="composer.datetime_submitted",
        help_text="The timestamp of when this request was submitted",
        required=False,
    )
    tracking_id = serializers.ReadOnlyField(
        source="current_tracking_id",
        help_text="The current tracking ID the agency has assigned to this request",
        required=False,
    )

    class Meta:
        model = FOIARequest
        fields = (
            # request details
            "id",
            "title",
            "slug",
            "status",
            "agency",
            "embargo",
            "permanent_embargo",
            "user",
            "edit_collaborators",
            "read_collaborators",
            # request dates
            "datetime_submitted",
            "datetime_updated",
            "datetime_done",
            # processing details
            "tracking_id",
            "price",
            # connected models
            # "tags",
            # "notes", # XXX
            # "communications", # XXX
        )
        extra_kwargs = {
            "edit_collaborators": {
                "help_text": "The IDs of the users who have been given edit access to "
                "this request"
            },
            "read_collaborators": {
                "help_text": "The IDs of the users who have been given view access to "
                "this request"
            },
        }


class FOIARequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for filing a new request"""

    agencies = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.filter(status="approved"),
        many=True,
        required=True,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.none(),
        required=False,
    )
    requested_docs = serializers.CharField()

    class Meta:
        model = FOIARequest
        fields = (
            "agencies",
            "organization",
            "embargo",
            "permanent_embargo",
            "title",
            "requested_docs",
            # "attachments",
            # "edit_collaborators",
            # "read_collaborators",
            # "tags",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request", None)
        view = self.context.get("view", None)
        user = request and request.user
        authed = user and user.is_authenticated
        # are we currently generating the documentation
        docs = getattr(view, "swagger_fake_view", False)
        if authed:
            # set the valid organizations to those the current user is a member of
            self.fields["organization"].queryset = Organization.objects.filter(
                users=user
            )
        # remove embargo fields if the user does not have permission to set them
        if not docs and (not authed or not user.has_perm("foia.embargo_foiarequest")):
            self.fields.pop("embargo")
        if not docs and (
            not authed or not user.has_perm("foia.embargo_perm_foiarequest")
        ):
            self.fields.pop("permanent_embargo")

    def validate(self, attrs):
        # if permanent embargo is true, embargo must be true
        if attrs.get("permanent_embargo"):
            attrs["embargo"] = True
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example 1",
            value={
                "foia": 72048,
                "from_user": 4420,
                "to_user": 9670,
                "subject": "RE: Freedom of Information Act Request: test",
                "datetime": "2024-07-24T08:18:20.380927-04:00",
                "response": False,
                "autogenerated": True,
                "communication": "To Whom It May Concern:\n\nI wanted to follow up "
                "on the following Freedom of Information Act request, copied below, "
                "and originally submitted on April 29, 2021. Please let me know when "
                "I can expect to receive a response.\n\nThanks for your help, and let "
                "me know if further clarification is needed.\n\n\n",
                "status": None,
            },
        )
    ]
)
class FOIACommunicationSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Communication model"""

    foia = serializers.PrimaryKeyRelatedField(
        queryset=FOIARequest.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the associated request",
    )

    class Meta:
        model = FOIACommunication
        fields = [
            "foia",
            "from_user",
            "to_user",
            "subject",
            "datetime",
            "response",
            "autogenerated",
            "communication",
            "status",
        ]
        extra_kwargs = {
            "from_user": {
                "help_text": "The ID of the user who sent this communication"
            },
            "to_user": {
                "help_text": "The ID of the user this communication was sent to"
            },
        }
