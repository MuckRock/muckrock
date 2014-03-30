"""
Serilizers for the accounts application API
"""

from django.contrib.auth.models import User

from rest_framework import serializers

from muckrock.accounts.models import Profile, Statistics

# pylint: disable=R0903

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model"""

    class Meta:
        model = Profile
        exclude = ('user', 'follows_foia', 'follows_question', 'notifications')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile = ProfileSerializer(source='profile_set')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser',
                  'last_login', 'date_joined', 'groups', 'profile')


class StatisticsSerializer(serializers.ModelSerializer):
    """Serializer for Statistics model"""

    def __init__(self, *args, **kwargs):
        # pylint: disable=E1101
        # pylint: disable=E1002
        super(StatisticsSerializer, self).__init__(*args, **kwargs)
        if 'request' not in self.context or not self.context['request'].user.is_staff:
            staff_only = ('pro_users', 'pro_user_names', 'total_page_views', 'daily_requests_pro',
                          'daily_requests_community', 'daily_requests_beta', 'daily_articles')
            for field in staff_only:
                self.fields.pop(field)

    class Meta:
        model = Statistics
        fields = ('date', 'total_requests', 'total_requests_success', 'total_requests_denied',
                  'total_requests_draft', 'total_requests_submitted', 'total_requests_awaiting_ack',
                  'total_requests_awaiting_response', 'total_requests_awaiting_appeal',
                  'total_requests_fix_required', 'total_requests_payment_required',
                  'total_requests_no_docs', 'total_requests_partial', 'total_requests_abandoned',
                  'total_pages', 'total_users', 'total_agencies', 'total_fees', 'pro_users',
                  'pro_user_names', 'total_page_views', 'daily_requests_pro',
                  'daily_requests_community', 'daily_requests_beta', 'daily_articles')

