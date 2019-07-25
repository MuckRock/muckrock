"""
Serializers for the Crowdsource application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.crowdsource.models import CrowdsourceResponse
from muckrock.tags.models import Tag, parse_tags


class TagField(serializers.ListField):
    """Serializer field for tags"""

    child = serializers.CharField()

    def to_representation(self, data):
        return [t.name for t in data.all()]


class CrowdsourceResponseSerializer(serializers.ModelSerializer):
    """Serializer for the Crowdsource Response model"""

    values = serializers.SerializerMethodField()
    user = serializers.StringRelatedField(source='user.profile.full_name')
    ip_address = serializers.CharField()
    edit_user = serializers.StringRelatedField(
        source='edit_user.profile.full_name'
    )
    data = serializers.StringRelatedField(source='data.url')
    datetime = serializers.DateTimeField(format='%m/%d/%Y %I:%M %p')
    edit_datetime = serializers.DateTimeField(format='%m/%d/%Y %I:%M %p')
    tags = TagField()

    def __init__(self, *args, **kwargs):
        super(CrowdsourceResponseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request is None or not request.user.is_staff:
            self.fields.pop('ip_address')

    def create(self, validated_data):
        """Handle tags"""
        tags = validated_data.pop('tags', None)
        instance = super(CrowdsourceResponseSerializer,
                         self).create(validated_data)
        self._set_tags(instance, tags)
        return instance

    def update(self, instance, validated_data):
        """Handle tags"""
        tags = validated_data.pop('tags', None)
        instance = super(CrowdsourceResponseSerializer,
                         self).update(instance, validated_data)
        self._set_tags(instance, tags)
        return instance

    def _set_tags(self, instance, tags):
        """Set tags"""
        if tags is not None:
            tag_set = set()
            for tag in parse_tags(','.join(tags)):
                new_tag, _ = Tag.objects.get_or_create(name=tag)
                tag_set.add(new_tag)
            instance.tags.set(*tag_set)

    def get_values(self, obj):
        """Get the values to return"""
        # use `.all()` calls so they can be prefetched
        # form data in python
        fields = obj.crowdsource.fields.all()
        values = obj.values.all()
        field_values = {}
        field_labels = {}
        for field in fields:
            field_values[field.pk] = []
            field_labels[field.pk] = field.label
        for value in values:
            if value.value:
                field_values[value.field_id].append(value.value)
        return [{
            'field': field_labels[fpk],
            'value': ', '.join(field_values[fpk])
        } for fpk in field_labels]

    class Meta:
        model = CrowdsourceResponse
        fields = '__all__'
