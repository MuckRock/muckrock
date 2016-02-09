"""
Serilizers for the accounts application API
"""

from django.contrib.auth.models import User

from rest_framework import serializers

from muckrock.accounts.models import Profile, Statistics
from muckrock.jurisdiction.models import Jurisdiction

# pylint: disable=too-few-public-methods

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model"""
    location = serializers.PrimaryKeyRelatedField(
            queryset=Jurisdiction.objects.all(),
            style={'base_template': 'input.html'})

    class Meta:
        model = Profile
        exclude = ('user', 'notifications')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser',
                  'last_login', 'date_joined', 'groups', 'profile')


class StatisticsSerializer(serializers.ModelSerializer):
    """Serializer for Statistics model"""

    def __init__(self, *args, **kwargs):
        # pylint: disable=no-member
        # pylint: disable=super-on-old-class
        super(StatisticsSerializer, self).__init__(*args, **kwargs)
        if 'request' not in self.context or not self.context['request'].user.is_staff:
            staff_only = (
                    'pro_users',
                    'pro_user_names',
                    'total_page_views',
                    'daily_requests_pro',
                    'daily_requests_basic',
                    'daily_requests_beta',
                    'daily_requests_proxy',
                    'daily_requests_admin',
                    'daily_requests_org',
                    'daily_articles',
                    'total_tasks',
                    'total_unresolved_tasks',
                    'total_generic_tasks',
                    'total_unresolved_generic_tasks',
                    'total_orphan_tasks',
                    'total_unresolved_orphan_tasks',
                    'total_snailmail_tasks',
                    'total_unresolved_snailmail_tasks',
                    'total_rejected_tasks',
                    'total_unresolved_rejected_tasks',
                    'total_staleagency_tasks',
                    'total_unresolved_staleagency_tasks',
                    'total_flagged_tasks',
                    'total_unresolved_flagged_tasks',
                    'total_newagency_tasks',
                    'total_unresolved_newagency_tasks',
                    'total_response_tasks',
                    'total_unresolved_response_tasks',
                    'total_faxfail_tasks',
                    'total_unresolved_faxfail_tasks',
                    'total_payment_tasks',
                    'total_unresolved_payment_tasks',
                    'total_crowdfundpayment_tasks',
                    'total_unresolved_crowdfundpayment_tasks',
                    'daily_robot_tasks',
                    'admin_notes',
                    'total_active_org_members',
                    'total_active_orgs',
                    )
            for field in staff_only:
                self.fields.pop(field)

    class Meta:
        model = Statistics
        fields = (
                'date',
                'total_requests',
                'total_requests_success',
                'total_requests_denied',
                'total_requests_draft',
                'total_requests_submitted',
                'total_requests_awaiting_ack',
                'total_requests_awaiting_response',
                'total_requests_awaiting_appeal',
                'total_requests_fix_required',
                'total_requests_payment_required',
                'total_requests_no_docs',
                'total_requests_partial',
                'total_requests_abandoned',
                'total_pages',
                'total_users',
                'total_agencies',
                'total_fees',
                'pro_users',
                'pro_user_names',
                'total_page_views',
                'daily_requests_pro',
                'daily_requests_basic',
                'daily_requests_beta',
                'daily_requests_proxy',
                'daily_requests_admin',
                'daily_requests_org',
                'daily_articles',
                'total_tasks',
                'total_unresolved_tasks',
                'total_generic_tasks',
                'total_unresolved_generic_tasks',
                'total_orphan_tasks',
                'total_unresolved_orphan_tasks',
                'total_snailmail_tasks',
                'total_unresolved_snailmail_tasks',
                'total_rejected_tasks',
                'total_unresolved_rejected_tasks',
                'total_staleagency_tasks',
                'total_unresolved_staleagency_tasks',
                'total_flagged_tasks',
                'total_unresolved_flagged_tasks',
                'total_newagency_tasks',
                'total_unresolved_newagency_tasks',
                'total_response_tasks',
                'total_unresolved_response_tasks',
                'total_faxfail_tasks',
                'total_unresolved_faxfail_tasks',
                'total_payment_tasks',
                'total_unresolved_payment_tasks',
                'total_crowdfundpayment_tasks',
                'total_unresolved_crowdfundpayment_tasks',
                'daily_robot_tasks',
                'public_notes',
                'admin_notes',
                'total_active_org_members',
                'total_active_orgs',
                )

