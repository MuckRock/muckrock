"""
Serializers for the Crowdsource application API
"""

# Standard Library
from collections import OrderedDict

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.crowdsource.fields import STATIC_FIELDS
from muckrock.crowdsource.models import CrowdsourceResponse
from muckrock.tags.models import Tag, parse_tags


class TagField(serializers.ListField):
    """Serializer field for tags"""

    child = serializers.CharField()

    def to_representation(self, data):
        return [t.name for t in data.all()]


class CrowdsourceResponseBaseSerializer(serializers.ModelSerializer):
    """Base serializer for Crowdsource Response model"""

    values = serializers.SerializerMethodField()
    edit_user = serializers.StringRelatedField(source="edit_user.profile.full_name")
    data = serializers.StringRelatedField(source="data.url")
    datetime = serializers.DateTimeField(format="%m/%d/%Y %I:%M %p")
    edit_datetime = serializers.DateTimeField(format="%m/%d/%Y %I:%M %p")

    show_all = False

    def get_values(self, obj):
        """Get the values to return"""
        # use `.all()` calls so they can be prefetched
        # form data in python
        fields = obj.crowdsource.fields.all()
        values = obj.values.all()
        field_values = {}
        field_labels = OrderedDict()
        for field in fields:
            if (field.gallery or self.show_all) and field.type not in STATIC_FIELDS:
                field_values[field.pk] = []
                field_labels[field.pk] = str(field)
        for value in values:
            if value.value and value.field_id in field_values:
                field_values[value.field_id].append(value.value)
        return [
            {"field": field_labels[fpk], "value": ", ".join(field_values[fpk])}
            for fpk in field_labels
        ]


class CrowdsourceResponseAdminSerializer(CrowdsourceResponseBaseSerializer):
    """Serializer for the Crowdsource Response model for Crowdsource administrators"""

    user = serializers.StringRelatedField(source="user.profile.full_name")
    ip_address = serializers.CharField()
    tags = TagField()

    show_all = True

    def __init__(self, *args, **kwargs):
        super(CrowdsourceResponseAdminSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request", None)
        if request is None or not request.user.is_staff:
            self.fields.pop("ip_address")

    def create(self, validated_data):
        """Handle tags"""
        tags = validated_data.pop("tags", None)
        instance = super(CrowdsourceResponseAdminSerializer, self).create(
            validated_data
        )
        self._set_tags(instance, tags)
        return instance

    def update(self, instance, validated_data):
        """Handle tags"""
        tags = validated_data.pop("tags", None)
        instance = super(CrowdsourceResponseAdminSerializer, self).update(
            instance, validated_data
        )
        self._set_tags(instance, tags)
        return instance

    def _set_tags(self, instance, tags):
        """Set tags"""
        if tags is not None:
            tag_set = set()
            for tag in parse_tags(",".join(tags)):
                new_tag, _ = Tag.objects.get_or_create(name=tag)
                tag_set.add(new_tag)
            instance.tags.set(tag_set)

    class Meta:
        model = CrowdsourceResponse
        fields = "__all__"


class CrowdsourceResponseGallerySerializer(CrowdsourceResponseBaseSerializer):
    """Serializer for the public gallery view of the Crowdsource Response model"""

    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        """Only show user's name if they chose to be publically credited"""
        if obj.public and obj.user:
            return obj.user.profile.full_name
        else:
            return "Anonymous"

    class Meta:
        model = CrowdsourceResponse
        fields = [
            "crowdsource",
            "user",
            "datetime",
            "data",
            "edit_user",
            "edit_datetime",
            "values",
        ]
