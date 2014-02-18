"""
Serilizers for the FOIA application API
"""

from rest_framework import serializers, permissions

from muckrock.foia.models import FOIARequest, FOIACommunication, FOIAFile, FOIANote

# Nest communications and files in here
# pylint: disable=R0903

class FOIAPermissions(permissions.DjangoModelPermissionsOrAnonReadOnly):
    """
    Object-level permission to allow owners of an object partially update it
    Also allows authenticated users to submit requests
    Assumes the model instance has a `user` attribute.
    """

    def has_permission(self, request, view):
        """Allow authenticated users to submit requests"""
        if request.user.is_authenticated() and request.method == 'POST':
            return True
        return super(FOIAPermissions, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        """Grant permission?"""
        # Instance must have an attribute named `user`.
        if obj.user == request.user and request.method == 'PATCH':
            return True
        return super(FOIAPermissions, self).has_object_permission(request, view, obj)

class IsOwner(permissions.BasePermission):
    """
    Object-level permission to allow access only to owners of an object
    """

    def has_object_permission(self, request, view, obj):
        """Grant permission?"""
        # Instance must have an attribute named `user`.
        if obj.user == request.user:
            return True
        else:
            return False


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

class FOIANoteSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Note model"""
    class Meta:
        model = FOIANote
        exclude = ('foia',)


class FOIARequestSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Request model"""
    user = serializers.RelatedField()
    tags = serializers.RelatedField(many=True)
    communications = FOIACommunicationSerializer(many=True)
    notes = FOIANoteSerializer(many=True)

    def __init__(self, *args, **kwargs):
        # pylint: disable=E1101
        # pylint: disable=E1002
        super(FOIARequestSerializer, self).__init__(*args, **kwargs)
        if args:
            foia = args[0]
        else:
            foia = None
        request = self.context['request']

        if not request.user.is_staff:
            self.fields.pop('mail_id')

        if foia and request.user != foia.user and not request.user.is_staff:
            self.fields.pop('notes')
        if not foia:
            self.fields.pop('notes')

        if foia and request.method == ['PATCH'] and request.user == foia.user \
                and not request.user.is_staff:
            # they may only update notes, tags, and embargo
            # XXX test
            for field in ('id', 'user', 'title', 'slug', 'status', 'communications', 'jurisdiction',
                          'agency', 'date_submitted', 'date_done', 'date_due', 'days_until_due',
                          'date_followup', 'date_embargo', 'price', 'requested_docs',
                          'description', 'tracking_id', 'mail_id'):
                self.fields.pop(field)

    class Meta:
        model = FOIARequest
        fields = ('id', 'user', 'title', 'slug', 'status', 'communications', 'jurisdiction',
                  'agency', 'date_submitted', 'date_done', 'date_due', 'days_until_due',
                  'date_followup', 'embargo', 'date_embargo', 'price', 'requested_docs',
                  'description', 'tracking_id', 'tags', 'mail_id', 'notes')
