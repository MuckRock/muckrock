"""
Serializers for the accounts application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.accounts.models import Profile, Statistics
from muckrock.organization.models import Organization

# pylint:disable = too-few-public-methods


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Example User",
            value={
                "id": 1,
                "username": "jdoe",
                "email": "jdoe@example.com",
                "last_login": "2023-10-20T12:34:56Z",
                "date_joined": "2023-01-01T00:00:00Z",
                "full_name": "John Doe",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
            },
        )
    ]
)
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with relevant Profile fields."""

    full_name = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source="profile.full_name",
        style={"base_template": "input.html"},
        help_text="The full name of the user",
    )
    uuid = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        source="profile.uuid",
        style={"base_template": "input.html"},
        help_text="The UUID of the user's profile",
    )
    organizations = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        many=True,
        required=False,
        help_text="The IDs of the organizations the user belongs to",
    )

    organizations = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        many=True,
        required=False,
        help_text="The IDs of the organizations the user belongs to",
    )

    class Meta:
        """Fields"""

        model = User
        fields = (
            "id",
            "username",
            "email",
            "last_login",
            "date_joined",
            "full_name",
            "uuid",
            "organizations",
        )
        extra_kwargs = {
            "id": {"help_text": "The unique identifier for the user"},
            "username": {"help_text": "The unique username of the user."},
            "email": {"help_text": "The email address of the user."},
            "last_login": {"help_text": "The last time the user logged in."},
            "date_joined": {"help_text": "The date and time when the user joined."},
            "full_name": {"help_text": "The full name of the user."},
            "uuid": {
                "help_text": "The unique identifier (UUID) of the user's profile."
            },
        }


class StatisticsSerializer(serializers.ModelSerializer):
    """Serializer for Statistics model"""

    class Meta:
        model = Statistics
        fields = (
            "date",
            "total_requests",
            "total_requests_success",
            "total_requests_denied",
            "total_requests_draft",
            "total_requests_submitted",
            "total_requests_awaiting_ack",
            "total_requests_awaiting_response",
            "total_requests_awaiting_appeal",
            "total_requests_fix_required",
            "total_requests_payment_required",
            "total_requests_no_docs",
            "total_requests_partial",
            "total_requests_abandoned",
            "total_requests_lawsuit",
            "requests_processing_days",
            "total_pages",
            "total_users",
            "total_agencies",
            "total_fees",
            "pro_users",
            "pro_user_names",
            "total_page_views",
            "daily_requests_pro",
            "daily_requests_basic",
            "daily_requests_beta",
            "daily_requests_proxy",
            "daily_requests_admin",
            "daily_requests_org",
            "daily_articles",
            "total_tasks",
            "total_unresolved_tasks",
            "total_generic_tasks",
            "total_unresolved_generic_tasks",
            "total_orphan_tasks",
            "total_unresolved_orphan_tasks",
            "total_snailmail_tasks",
            "total_unresolved_snailmail_tasks",
            "total_rejected_tasks",
            "total_unresolved_rejected_tasks",
            "total_staleagency_tasks",
            "total_unresolved_staleagency_tasks",
            "total_flagged_tasks",
            "total_unresolved_flagged_tasks",
            "total_newagency_tasks",
            "total_unresolved_newagency_tasks",
            "total_response_tasks",
            "total_unresolved_response_tasks",
            "total_faxfail_tasks",
            "total_unresolved_faxfail_tasks",
            "total_payment_tasks",
            "total_unresolved_payment_tasks",
            "total_crowdfundpayment_tasks",
            "total_unresolved_crowdfundpayment_tasks",
            "total_reviewagency_tasks",
            "total_unresolved_reviewagency_tasks",
            "daily_robot_response_tasks",
            "public_notes",
            "admin_notes",
            "total_active_org_members",
            "total_active_orgs",
            "sent_communications_email",
            "sent_communications_fax",
            "sent_communications_mail",
            "total_users_filed",
            "flag_processing_days",
            "unresolved_snailmail_appeals",
            "total_crowdfunds",
            "total_crowdfunds_pro",
            "total_crowdfunds_basic",
            "total_crowdfunds_beta",
            "total_crowdfunds_proxy",
            "total_crowdfunds_admin",
            "open_crowdfunds",
            "open_crowdfunds_pro",
            "open_crowdfunds_basic",
            "open_crowdfunds_beta",
            "open_crowdfunds_proxy",
            "open_crowdfunds_admin",
            "closed_crowdfunds_0",
            "closed_crowdfunds_0_25",
            "closed_crowdfunds_25_50",
            "closed_crowdfunds_50_75",
            "closed_crowdfunds_75_100",
            "closed_crowdfunds_100_125",
            "closed_crowdfunds_125_150",
            "closed_crowdfunds_150_175",
            "closed_crowdfunds_175_200",
            "closed_crowdfunds_200",
            "total_crowdfund_payments",
            "total_crowdfund_payments_loggedin",
            "total_crowdfund_payments_loggedout",
            "public_projects",
            "private_projects",
            "unapproved_projects",
            "crowdfund_projects",
            "project_users",
            "project_users_pro",
            "project_users_basic",
            "project_users_beta",
            "project_users_proxy",
            "project_users_admin",
            "total_exemptions",
            "total_invoked_exemptions",
            "total_example_appeals",
            "total_crowdsources",
            "total_draft_crowdsources",
            "total_open_crowdsources",
            "total_close_crowdsources",
            "num_crowdsource_responded_users",
            "total_crowdsource_responses",
            "crowdsource_responses_pro",
            "crowdsource_responses_basic",
            "crowdsource_responses_beta",
            "crowdsource_responses_proxy",
            "crowdsource_responses_admin",
            "machine_requests",
            "machine_requests_success",
            "machine_requests_denied",
            "machine_requests_draft",
            "machine_requests_submitted",
            "machine_requests_awaiting_ack",
            "machine_requests_awaiting_response",
            "machine_requests_awaiting_appeal",
            "machine_requests_fix_required",
            "machine_requests_payment_required",
            "machine_requests_no_docs",
            "machine_requests_partial",
            "machine_requests_abandoned",
            "machine_requests_lawsuit",
        )
