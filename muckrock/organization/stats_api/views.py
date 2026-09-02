# Django
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware

# Standard Library
from datetime import timedelta

# Third Party
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

# MuckRock
from muckrock.core.pagination import CursorPagination
from muckrock.organization.stats_api.models import OrganizationStats
from muckrock.organization.stats_api.serializers import OrganizationStatsSerializer


class OrganizationStatsFilter(django_filters.FilterSet):
    """Staff-facing activity filters for organization stats."""

    active_within_days = django_filters.NumberFilter(
        method="filter_active_within_days",
        label="Active in last N days (filed a request)",
        help_text="Return organizations that filed a request within the last N days.",
    )
    filed_within_days = django_filters.NumberFilter(
        method="filter_filed_within_days",
        label="Filed in last N days",
        help_text="Return organizations that filed a request in the last N days.",
    )

    class Meta:
        model = OrganizationStats
        fields = []

    @staticmethod
    def _cutoff(value):
        return timezone.now() - timedelta(days=int(value))

    def filter_filed_within_days(self, queryset, _name, value):
        return queryset.filter(last_request_at__gte=self._cutoff(value))

    # No login concept for an org, so "active" is just "filed recently."
    filter_active_within_days = filter_filed_within_days


class OrganizationStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff-facing organization activity stats."""

    serializer_class = OrganizationStatsSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CursorPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrganizationStatsFilter
    lookup_field = "organization__uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        # Bare cursor scan; individual orgs are excluded (no org-side stats).
        return (
            OrganizationStats.objects.select_related("organization")
            .exclude(organization__individual=True)
            .order_by("pk")
        )

    def _annotate_and_prefetch(self, queryset):
        cutoff = timezone.now() - timedelta(days=settings.REQUEST_WINDOW_DAYS)
        return (
            queryset.select_related("organization", "organization__parent")
            .prefetch_related("organization__groups")
            .annotate(
                total_requests=Count(
                    "organization__composers__foias",
                    filter=~Q(organization__composers__status="started"),
                    distinct=True,
                ),
                recent_request_count=Count(
                    "organization__composers__foias",
                    filter=Q(organization__composers__datetime_submitted__gte=cutoff),
                    distinct=True,
                ),
            )
        )

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is None:
            return None
        annotated = self._annotate_and_prefetch(
            OrganizationStats.objects.filter(pk__in=[o.pk for o in page])
        ).order_by("pk")
        return list(annotated)

    def get_object(self):
        obj = super().get_object()
        return self._annotate_and_prefetch(
            OrganizationStats.objects.filter(pk=obj.pk)
        ).get()

    @action(detail=False, methods=["get"])
    def aged_out(self, request):
        """Organizations with a request that crossed the recent-window boundary
        since `since`, so their recent-request count has dropped."""
        since = request.query_params.get("since")
        if not since:
            return Response({"error": "since query param is required"}, status=400)
        since_dt = parse_datetime(since)
        if since_dt is None:
            return Response({"error": "since must be an ISO 8601 datetime"}, status=400)
        if is_naive(since_dt):
            since_dt = make_aware(since_dt)
        win = timedelta(days=settings.REQUEST_WINDOW_DAYS)
        now = timezone.now()
        qs = (
            self.get_queryset()
            .filter(
                organization__composers__datetime_submitted__gte=since_dt - win,
                organization__composers__datetime_submitted__lt=now - win,
            )
            .distinct()
        )
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
