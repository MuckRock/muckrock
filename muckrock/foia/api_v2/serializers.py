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
from muckrock.foia.models import FOIACommunication, FOIARequest, FOIANote
from muckrock.organization.models import Organization
from muckrock.foia.models.file import FOIAFile


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
                "embargo_status": "public",
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
            "embargo_status",  # public, embargo, or permanent
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
            "embargo_status",
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
            self.fields.pop("embargo_status")
    # If the user doesn't have the permission to set to a permanent embargo, tell them. 
    def validate_embargo_status(self, value):
        request = self.context.get("request", None)
        if value == "permanent" and not request.user.has_perm(
            "foia.embargo_perm_foiarequest", self.instance
        ):
            raise serializers.ValidationError(
                "You do not have permission to set embargo to permanent"
            )
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "FOIA File Example",
            value={
                "id": 1215939,
                "ffile": "https://cdn.muckrock.com/foia_files/2024/09/05/PSP_FINAL_RESPONSE_RTK__2024-1657_xLBSvYT.pdf",
                "datetime": "2024-09-05T14:01:29.268029",
                "title": "PSP FINAL RESPONSE RTK # 2024-1657",
                "source": "Pennsylvania State Police, Pennsylvania",
                "description": "",
                "doc_id": "25092350-psp-final-response-rtk-2024-1657",
                "pages": 11,
            },
        )
    ]
)
class FOIAFileSerializer(serializers.ModelSerializer):
    """Serializer for FOIA File model"""

    ffile = serializers.SerializerMethodField()
    datetime = serializers.DateTimeField()
    title = serializers.CharField()
    source = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    doc_id = serializers.CharField()
    pages = serializers.IntegerField()

    class Meta:
        model = FOIAFile
        exclude = ("comm",)  # Exclude communications

    def get_ffile(self, obj):
        """Get the ffile URL safely"""
        if obj.ffile and hasattr(obj.ffile, "url"):
            return obj.ffile.url
        else:
            return ""


class FOIANoteSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Note model"""

    datetime = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FOIANote
        exclude = ("id", "foia")


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

    files = FOIAFileSerializer(many=True)
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
            "files",
        ]
        extra_kwargs = {
            "from_user": {
                "help_text": "The ID of the user who sent this communication"
            },
            "to_user": {
                "help_text": "The ID of the user this communication was sent to"
            },
        }
