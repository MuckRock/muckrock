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
from muckrock.foia.models import FOIARequest


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
