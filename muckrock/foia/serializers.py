"""
Serilizers for the FOIA application API
"""

from rest_framework import serializers, permissions

from muckrock.foia.models import FOIARequest, FOIACommunication, FOIAFile

# Nest communications and files in here
# pylint: disable=R0903

class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or staff to edit it.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        """Grant permission?"""
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # If the user is staff always allow
        if request.user.is_staff:
            return True

        # Instance must have an attribute named `user`.
        return obj.user == request.user


class FOIAFileSerializer(serializers.ModelSerializer):
    """Serializer for FOIA File model"""
    ffile = serializers.CharField(source='ffile.url', read_only=True)
    class Meta:
        model = FOIAFile
        exclude = ('foia', 'comm')


class FOIACommunicationSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Communication model"""
    files = FOIAFileSerializer(many=True)
    class Meta:
        model = FOIACommunication
        exclude = ('foia',)


class FOIARequestSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Request model"""
    user = serializers.RelatedField()
    tags = serializers.RelatedField(many=True)
    communications = FOIACommunicationSerializer(many=True)
    class Meta:
        model = FOIARequest
        fields = ('id', 'user', 'title', 'slug', 'status', 'communications', 'jurisdiction',
                  'agency', 'date_submitted', 'date_done', 'date_due', 'days_until_due',
                  'date_followup', 'embargo', 'date_embargo', 'price', 'requested_docs',
                  'description', 'tracking_id', 'tags')
