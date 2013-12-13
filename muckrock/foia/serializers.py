"""
Serilizers for the FOIA application API
"""

from rest_framework import serializers

from muckrock.foia.models import FOIARequest

# Nest communications and files in here
# pylint: disable=R0903

class FOIARequestSerializer(serializers.ModelSerializer):
    """Serializer for FOIA Request model"""
    user = serializers.RelatedField()
    tags = serializers.RelatedField(many=True)
    class Meta:
        model = FOIARequest
        fields = ('id', 'user', 'title', 'slug', 'status', 'jurisdiction', 'agency',
                  'date_submitted', 'date_done', 'date_due', 'days_until_due', 'date_followup',
                  'price', 'requested_docs', 'description', 'tracking_id', 'email',
                  'other_emails', 'tags')


