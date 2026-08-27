# Django
from django.utils import timezone

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.organization.stats_api.models import OrganizationStats


class OrganizationStatsSerializer(serializers.ModelSerializer):
    """Staff-facing organization activity stats."""

    uuid = serializers.UUIDField(source="organization.uuid", read_only=True)
    name = serializers.CharField(source="organization.name", read_only=True)
    total_requests = serializers.SerializerMethodField(
        help_text="Total non-draft requests filed by the organization."
    )
    recent_request_count = serializers.SerializerMethodField(
        help_text="Requests filed within the configured recent window "
        "(REQUEST_WINDOW_DAYS, currently defaults to 90)."
    )
    days_since_last_request = serializers.SerializerMethodField(
        help_text="Days since the organization last filed a request."
    )
    requests = serializers.SerializerMethodField(
        help_text="Pooled request balance across shared organizations."
    )

    class Meta:
        model = OrganizationStats
        fields = [
            "uuid",
            "name",
            "last_request_at",
            "total_requests",
            "recent_request_count",
            "days_since_last_request",
            "requests",
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

    def get_requests(self, obj):
        org = obj.organization
        return {
            "requests_per_month": org.get_total_requests_per_month(),
            "monthly_requests": org.get_total_monthly_requests(),
            "number_requests": org.get_total_number_requests(),
        }
