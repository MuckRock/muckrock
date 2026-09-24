"""
Provides a pagination class for the API
"""

# Django
from django.conf import settings

# Third Party
from rest_framework import pagination
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import remove_query_param


class StandardPagination(PageNumberPagination):
    """Defines default and maximum page size for pagination"""

    page_size = settings.DEFAULT_PAGE_SIZE
    max_page_size = settings.MAX_PAGE_SIZE
    page_size_query_param = "page_size"


class CursorPagination(pagination.CursorPagination):
    """Cursor-based pagination ordered by pk.

    Ordered by pk so it works for any model without requiring a timestamp field.
    """

    ordering = "pk"
    page_size = settings.DEFAULT_PAGE_SIZE
    max_page_size = settings.MAX_PAGE_SIZE
    page_size_query_param = "per_page"


class APIV2CursorPagination(CursorPagination):
    """
    Custom cursor pagination class for the public APIv2.
    Uses page_size as the page size query param to preserve
    legacy callers, uses a different max page size than the
    stats api set in env vars, and allows for count to be returned
    in one of 3 modes depending on the API_PAGINATION_COUNT_MODE variable.
    0 = return no count at all
    1 = return count if count=1 is specified in calls.
        No stripping of this count=1 on next/previous
    2 = return count if count=1 is specified in calls and strips the count parameter
        from next/previous. This allows for explicit count calls
        but removes it from the next/previous response
        so that this cost isn't paid on each next/previous.
    In every mode, count values other than "1" raise a 400.
    In mode 0, count=1 is accepted but ignored.
    """

    max_page_size = settings.APIV2_MAX_PAGE_SIZE
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        value = request.query_params.get("count")
        if value not in (None, "1"):
            raise ValidationError({"count": "Pass count=1 to include the total count."})

        mode = settings.API_PAGINATION_COUNT_MODE
        if value == "1" and mode != 0:
            self.include_count = True
            self.count = queryset.count()
        else:
            self.include_count = False

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if self.include_count:
            response.data["count"] = self.count
        return response

    def get_next_link(self):
        return self.strip_count(super().get_next_link())

    def get_previous_link(self):
        return self.strip_count(super().get_previous_link())

    def strip_count(self, link):
        if link and settings.API_PAGINATION_COUNT_MODE == 2:
            return remove_query_param(link, "count")
        return link
