# Django
from django.conf import settings
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

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
from muckrock.accounts.stats_api.models import UserStats
from muckrock.accounts.stats_api.serializers import UserStatsSerializer
from muckrock.core.pagination import CursorPagination
from muckrock.organization.models import Organization


class UserStatsFilter(django_filters.FilterSet):
    """Staff-facing activity filters for user stats."""

    active_within_days = django_filters.NumberFilter(
        method="filter_active_within_days",
        label="Active in last N days (filed or login)",
        help_text=(
            "Return users who filed a request" " or logged in within the last N days."
        ),
    )
    filed_within_days = django_filters.NumberFilter(
        method="filter_filed_within_days",
        label="Filed in last N days",
        help_text="Return users who filed a request in the last N days.",
    )
    logged_in_within_days = django_filters.NumberFilter(
        method="filter_logged_in_within_days",
        label="Logged in within last N days",
        help_text="Return users whose most recent login was within the last N days.",
    )

    class Meta:
        model = UserStats
        fields = []

    @staticmethod
    def _cutoff(value):
        return timezone.now() - timedelta(days=int(value))

    def filter_filed_within_days(self, queryset, _name, value):
        return queryset.filter(last_request_at__gte=self._cutoff(value))

    def filter_logged_in_within_days(self, queryset, _name, value):
        return queryset.filter(user__last_login__gte=self._cutoff(value))

    def filter_active_within_days(self, queryset, _name, value):
        cutoff = self._cutoff(value)
        return queryset.filter(
            Q(last_request_at__gte=cutoff) | Q(user__last_login__gte=cutoff)
        )


class UserStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff-facing user activity stats."""

    serializer_class = UserStatsSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CursorPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserStatsFilter
    lookup_field = "user__profile__uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        # Bare cursor scan — no annotation/prefetch here. Enrichment is applied
        # only to the current page in paginate_queryset / get_object.
        return UserStats.objects.select_related("user").order_by("pk")

    def _annotate_and_prefetch(self, queryset):
        cutoff = timezone.now() - timedelta(days=settings.REQUEST_WINDOW_DAYS)
        return (
            queryset.select_related("user", "user__profile")
            .prefetch_related(
                Prefetch(
                    "user__organizations",
                    queryset=Organization.objects.filter(individual=True),
                    to_attr="individual_orgs",
                )
            )
            .annotate(
                total_requests=Count(
                    "user__composers__foias",
                    filter=~Q(user__composers__status="started"),
                    distinct=True,
                ),
                recent_request_count=Count(
                    "user__composers__foias",
                    filter=Q(user__composers__datetime_submitted__gte=cutoff),
                    distinct=True,
                ),
            )
        )

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is None:
            return None
        annotated = self._annotate_and_prefetch(
            UserStats.objects.filter(pk__in=[u.pk for u in page])
        ).order_by("pk")
        return list(annotated)

    def get_object(self):
        obj = super().get_object()
        return self._annotate_and_prefetch(UserStats.objects.filter(pk=obj.pk)).get()

    @action(detail=False, methods=["get"])
    def aged_out(self, request):
        """Users with a request that crossed the recent-window boundary since
        `since`, so their recent-request count has dropped and needs
        re-syncing."""
        since = request.query_params.get("since")
        if not since:
            return Response({"error": "since query param is required"}, status=400)
        since_dt = parse_datetime(since)
        if since_dt is None:
            return Response({"error": "since must be an ISO 8601 datetime"}, status=400)
        win = timedelta(days=settings.REQUEST_WINDOW_DAYS)
        now = timezone.now()
        qs = (
            self.get_queryset()
            .filter(
                user__composers__datetime_submitted__gte=since_dt - win,
                user__composers__datetime_submitted__lt=now - win,
            )
            .distinct()
        )
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
