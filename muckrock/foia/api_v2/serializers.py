"""
Serilizers for V2 of the FOIA API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.foia.models import FOIARequest


class FOIARequestSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Request model"""

    user = serializers.PrimaryKeyRelatedField(
        source="composer.user",
        queryset=User.objects.all(),
        style={"base_template": "input.html"},
    )
    datetime_submitted = serializers.DateTimeField(
        read_only=True, source="composer.datetime_submitted"
    )
    tracking_id = serializers.ReadOnlyField(source="current_tracking_id")

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
