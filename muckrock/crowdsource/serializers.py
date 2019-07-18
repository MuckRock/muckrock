"""
Serializers for the Crowdsource application API
"""

# Django
from django.contrib.postgres.aggregates.general import StringAgg
from django.db.models import F

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.crowdsource.models import CrowdsourceResponse, CrowdsourceValue
from muckrock.tags.models import Tag, parse_tags


class TagField(serializers.ListField):
    """Serializer field for tags"""

    child = serializers.CharField()

    def to_representation(self, data):
        return data.values_list('name', flat=True)


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
        return list(
            obj.values.order_by('field__order')
            # group by field, rename so we can shadow it later
            .values(field_id=F('field'))
            # concat all values for the same field with commas
            .annotate(value=StringAgg('value', ', '))
            # select the concated value and the field label
            .values('value', field=F('field__label'))
        )

    class Meta:
        model = CrowdsourceResponse
        fields = '__all__'
