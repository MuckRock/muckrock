# Django
from django.utils import timezone

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.accounts.stats_api.models import UserStats


class UserStatsSerializer(serializers.ModelSerializer):
    """Staff-facing user activity stats."""

    uuid = serializers.UUIDField(source="user.profile.uuid", read_only=True)
    last_login_at = serializers.DateTimeField(source="user.last_login", read_only=True)
    total_requests = serializers.SerializerMethodField(
        help_text="Total non-draft requests the user has filed."
    )
    recent_request_count = serializers.SerializerMethodField(
        help_text="Number of requests filed within the configured recent window "
        "(REQUEST_WINDOW_DAYS, currently defaults to 90)."
    )
    days_since_last_request = serializers.SerializerMethodField(
        help_text="Number of days since the user last filed a request."
    )
    individual_requests = serializers.SerializerMethodField()

    class Meta:
        model = UserStats
        fields = [
            "uuid",
            "last_request_at",
            "last_login_at",
            "total_requests",
            "recent_request_count",
            "days_since_last_request",
            "individual_requests",
        ]
        read_only_fields = fields

    def get_total_requests(self, obj):
        return getattr(obj, "total_requests", None)

    def get_recent_request_count(self, obj):
        return getattr(obj, "recent_request_count", None)

    def get_days_since_last_request(self, obj):
        if obj.last_request_at is None:
            return None
        return (timezone.now() - obj.last_request_at).days

    def get_individual_requests(self, obj):
        orgs = getattr(obj.user, "individual_orgs", [])
        if not orgs:
            return None
        org = orgs[0]
        return {
            "requests_per_month": org.requests_per_month,
            "monthly_requests": org.monthly_requests,
            "number_requests": org.number_requests,
        }
