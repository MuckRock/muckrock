"""
Serilizers for the Agency application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""
    types = serializers.StringRelatedField(many=True)
    appeal_agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        style={'base_template': 'input.html'},
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(),
        style={'base_template': 'input.html'},
    )
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(),
        style={'base_template': 'input.html'},
    )
    location = serializers.JSONField()
    absolute_url = serializers.ReadOnlyField(source='get_absolute_url')
    average_response_time = serializers.ReadOnlyField()
    fee_rate = serializers.ReadOnlyField()
    success_rate = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        """After initializing the serializer,
        check that the current user has permission
        to view agency email data."""
        # pylint: disable=super-on-old-class
        super(AgencySerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request is None or not request.user.is_staff:
            # email and other_emails no longer exists
            # keeping logic here for future use
            self.fields.pop('email', None)
            self.fields.pop('other_emails', None)

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
            'requires_proxy',
            # location
            'jurisdiction',
            'location',
            # contact info
            'website',
            'twitter',
            'twitter_handles',
            # connects to other agencies
            'parent',
            'appeal_agency',
            # describes agency foia process
            'url',
            'foia_logs',
            'foia_guide',
            # misc
            'public_notes',
            # computed fields
            'absolute_url',
            'average_response_time',
            'fee_rate',
            'success_rate',
        )
