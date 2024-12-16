"""
Serilizers for V2 of the FOIA API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.foia.models.file import FOIAFile
from muckrock.organization.models import Organization

# pylint:disable = too-few-public-methods


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "FOIA Request Response Example",
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
        help_text="The tracking ID assigned to this request by the agency",
        required=False,
    )

    class Meta:
        """Filters for foia request search"""

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
            # "notes",
            # "communications",
        )
        extra_kwargs = {
            "id": {"help_text": "The unique identifier for this FOIA request"},
            "title": {"help_text": "The title of the FOIA request"},
            "slug": {"help_text": "The slug (URL identifier) for the FOIA request"},
            "status": {"help_text": "The current status of the FOIA request"},
            "agency": {"help_text": "The ID of the agency handling this FOIA request"},
            "embargo_status": {
                "help_text": (
                    "The embargo status. "
                    "Embargo is only available to paid professional users and "
                    "permanent is only available to paid organizational members."
                )
            },
            "user": {"help_text": "The user who filed this FOIA request"},
            "edit_collaborators": {
                "help_text": "The users who have been given edit access to this request"
            },
            "read_collaborators": {
                "help_text": "The users who have been given view access to this request"
            },
            "datetime_submitted": {
                "help_text": "The date and time when the request was submitted"
            },
            "datetime_updated": {
                "help_text": "The date and time when the request was last updated"
            },
            "datetime_done": {
                "help_text": "The date and time when the request was completed, if applicable"
            },
            "price": {
                "help_text": "The cost of processing this request, if applicable"
            },
        }


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Create FOIARequest Example",
            value={
                "agencies": [2],
                "organization": 3,
                "embargo_status": "public",
                "title": "Request for Meeting Minutes",
                "requested_docs": "All meeting minutes from Q1 2023",
            },
        ),
        OpenApiExample(
            "Create FOIARequest Response Example",
            value={
                "id": 1,
                "title": "Request for Meeting Minutes",
                "slug": "meeting-minutes-1",
                "status": "processing",
                "agency": 2,
                "embargo_status": "public",
                "user": 3,
                "datetime_submitted": "2023-01-20T08:00:00Z",
                "datetime_updated": "2023-01-21T08:00:00Z",
                "datetime_done": None,
                "tracking_id": "ABC123-456",
                "price": "0.00",
            },
        ),
    ]
)
class FOIARequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for filing a new request"""

    agencies = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.filter(status="approved"),
        many=True,
        required=True,
        help_text="List of agency IDs of agencies you would like to send this request to.",
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.none(),
        required=False,
        help_text="ID of the organization submitting this request",
    )
    requested_docs = serializers.CharField(
        help_text="Description of the documents being requested"
    )

    class Meta:
        """Filters for foia request create"""

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
        extra_kwargs = {
            "embargo_status": {
                "help_text": (
                    "The embargo status for the request (e.g., public, embargo, permanent). "
                    "Embargo is only available to paid professional users and "
                    "permanent is only available to paid organizational members."
                )
            },
            "title": {"help_text": "The title of the FOIA request"},
        }

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

    def validate_embargo_status(self, value):
        """If the user doesn't have the permission to set to a permanent embargo, tell them"""
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
                "ffile": "https://cdn.muckrock.com/foia_files/2024/09/05/PSP_FINAL_RESPONSE_RTK__2024-1657_xLBSvYT.pdf",  # pylint: disable=line-too-long
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

    ffile = serializers.SerializerMethodField(help_text="The URL of the file")
    datetime = serializers.DateTimeField(
        help_text="The date and time when the file was uploaded"
    )
    title = serializers.CharField(help_text="The title of the file")
    source = serializers.CharField(
        help_text="The source of the file (e.g., the agency or department)"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="A description of the file",
    )
    doc_id = serializers.CharField(
        help_text="The document identifier assigned to the file"
    )
    pages = serializers.IntegerField(help_text="The number of pages in the file")

    class Meta:
        """Filters for foia files"""

        model = FOIAFile
        exclude = ("comm",)  # Exclude communications
        read_only_fields = (
            "ffile",
            "datetime",
            "title",
            "source",
            "description",
            "doc_id",
            "pages",
        )

    def get_ffile(self, obj) -> str:
        """Get the ffile URL safely"""
        if obj.ffile and hasattr(obj.ffile, "url"):
            return obj.ffile.url
        return ""


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

    files = serializers.PrimaryKeyRelatedField(
        queryset=FOIAFile.objects.all(),
        many=True,
        required=False,
        help_text="The list of file IDs associated with this communication",
    )
    foia = serializers.PrimaryKeyRelatedField(
        queryset=FOIARequest.objects.all(),
        style={"base_template": "input.html"},
        help_text="The ID of the associated request",
    )

    class Meta:
        """Filters for foia comms"""

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
            "foia": {
                "help_text": "The ID of the FOIA request associated with this communication"
            },
            "from_user": {"help_text": "The ID of the user sending this communication"},
            "to_user": {"help_text": "The ID of the user receiving this communication"},
            "subject": {"help_text": "The subject of the communication"},
            "datetime": {
                "help_text": "The date and time when the communication was sent"
            },
            "response": {"help_text": "Indicates if the communication is a response"},
            "autogenerated": {
                "help_text": ("Indicates if the communication was autogenerated")
            },
            "communication": {"help_text": "The content of the communication"},
            "status": {"help_text": "The status of the communication, if applicable"},
            "files": {
                "help_text": "The list of files associated with this communication"
            },
        }
