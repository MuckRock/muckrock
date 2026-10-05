"""
Provides a pagination class for the API
"""

# Django
from django.conf import settings

# Third Party
from rest_framework import pagination
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
    Cursor pagination for the public APIv2, using page_size to preserve legacy callers.

    Passing ?count includes the total count, depending on API_PAGINATION_COUNT_MODE:
    0 = never return a count
    1 = return a count when ?count is passed, and keep it on next/previous links
    2 = return a count when ?count is passed, but strip it from next/previous links
    """

    max_page_size = settings.APIV2_MAX_PAGE_SIZE
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        mode = settings.API_PAGINATION_COUNT_MODE
        self.include_count = "count" in request.query_params and mode != 0
        if self.include_count:
            self.count = queryset.count()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if self.include_count:
            response.data = {"count": self.count, **response.data}
        return response

    def get_next_link(self):
        return self.strip_count(super().get_next_link())

    def get_previous_link(self):
        return self.strip_count(super().get_previous_link())

    def strip_count(self, link):
        if link and settings.API_PAGINATION_COUNT_MODE == 2:
            return remove_query_param(link, "count")
        return link
