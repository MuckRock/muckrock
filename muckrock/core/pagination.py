"""
Provides a pagination class for the API
"""

# Django
from django.conf import settings

# Third Party
from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination


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
