"""
Serilizers for V2 of the FOIA API
"""

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.organization.models import Organization


class EmbargoMixin:
    """Embargo validators for all FOIA Request serializers"""

    def validate_embargo(self, value):
        request = self.context.get("request", None)
        user = request and request.user
        if value and not (user and user.has_perm("foia.embargo_foiarequest")):
            raise serializers.ValidationError(
                "You do not have permission to set `embargo`"
            )
        return value

    def validate_permanent_embargo(self, value):
        request = self.context.get("request", None)
        user = request and request.user
        if value and not (user and user.has_perm("foia.embargo_perm_foiarequest")):
            raise serializers.ValidationError(
                "You do not have permission to set `permanent_embargo`"
            )
        return value

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
                "tags": ["minutes"],
                "price": "0.00",
            },
            response_only=True,
        )
    ]
)
class FOIARequestSerializer(
    EmbargoMixin, TaggitSerializer, serializers.ModelSerializer
):
    """Serializer for FOIA Request model"""

    user = serializers.PrimaryKeyRelatedField(
        source="composer.user",
        style={"base_template": "input.html"},
        help_text="The user ID of the user who filed this request",
        read_only=True,
    )
    datetime_submitted = serializers.DateTimeField(
        source="composer.datetime_submitted",
        help_text="The timestamp of when this request was submitted",
        read_only=True,
    )
    tracking_id = serializers.CharField(
        source="current_tracking_id",
        help_text="The current tracking ID the agency has assigned to this request",
        read_only=True,
    )
    tags = TagListSerializerField(
        required=False,
        help_text="Tags associated with the request",
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
            "tags",
        )
        extra_kwargs = {
            "title": {"read_only": True},
            "slug": {"read_only": True},
            "status": {"read_only": True},
            "agency": {"read_only": True},
            "datetime_updated": {"read_only": True},
            "datetime_done": {"read_only": True},
            "price": {"read_only": True},
            "edit_collaborators": {
                "help_text": "The IDs of the users who have been given edit access to "
                "this request"
            },
            "read_collaborators": {
                "help_text": "The IDs of the users who have been given view access to "
                "this request"
            },
        }


class FOIARequestCreateSerializer(EmbargoMixin, serializers.ModelSerializer):
    """Serializer for filing a new request"""

    agencies = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.filter(status="approved"),
        many=True,
        required=True,
        help_text="A list of IDs for the agencies to file this request with.  "
        "Providing more than one agency ID allows you to file a single request "
        "with multiple agencies",
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.none(),
        required=False,
        help_text="The ID of one of your organizations that you want this request "
        "associated with.  This organization will be charged for the filing of "
        "this request.  If left blank, it will default to your current active "
        "organization",
    )
    requested_docs = serializers.CharField(
        help_text="A description of the documents you are requesting from the agency."
    )

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
        user = request and request.user
        authed = user and user.is_authenticated
        if authed:
            # set the valid organizations to those the current user is a member of
            self.fields["organization"].queryset = Organization.objects.filter(
                users=user
            )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Succesful",
            status_codes=[201],
            value={
                "status": "FOI Request submitted",
                "location": "https://www.muckrock.com/foi/multirequest/test-123/",
                "requests": [456],
            },
        ),
        OpenApiExample(
            "Payment required",
            status_codes=[402],
            value={
                "status": "Out of requests.  FOI Request has been saved.",
                "location": "https://www.muckrock.com/foi/multirequest/test-123/",
            },
        ),
    ]
)
class FOIARequestCreateReturnSerializer(serializers.Serializer):
    """Serializer for return data for creating a request"""

    # pylint: disable=abstract-method

    status = serializers.CharField(help_text="A description of the status.")
    location = serializers.URLField(help_text="The URL of the created request.")
    requests = serializers.PrimaryKeyRelatedField(
        queryset=FOIARequest.objects.all(),
        many=True,
        required=False,
        help_text="The IDs of the created requests",
    )


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
