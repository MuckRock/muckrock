"""
Serilizers for the Agency application API
"""

from rest_framework import serializers

from muckrock.agency.models import Agency

# pylint: disable=too-few-public-methods

class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""
    types = serializers.StringRelatedField(many=True)
    appeal_agency = serializers.PrimaryKeyRelatedField(
            queryset=Agency.objects.all(),
            style={'base_template': 'input.html'})
    parent = serializers.PrimaryKeyRelatedField(
            queryset=Agency.objects.all(),
            style={'base_template': 'input.html'})
    location = serializers.JSONField()

    def __init__(self, *args, **kwargs):
        """After initializing the serializer,
        check that the current user has permission
        to view agency email data."""
        # pylint: disable=super-on-old-class
        super(AgencySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request is None or not request.user.is_staff:
            self.fields.pop('email')
            self.fields.pop('other_emails')

    class Meta:
        model = Agency
        fields = (
            # describes agency
            'id',
            'name',
            'slug',
            'status',
            'stale',
            'exempt',
            'types',
            # location
            'jurisdiction',
            'address',
            'location',
            # contact info
            'email',
            'other_emails',
            'phone',
            'fax',
            'website',
            'twitter',
            'twitter_handles',
            # connects to other agencies
            'parent',
            'appeal_agency',
            'can_email_appeals',
            # describes agency foia process
            'url',
            'foia_logs',
            'foia_guide',
            # misc
            'public_notes',
        )
