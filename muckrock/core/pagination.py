"""
Provides a pagination class for the API
"""

# Django
from django.conf import settings

# Third Party
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Defines default and maximum page size for pagination"""

    page_size = 50
    max_page_size = settings.MAX_PAGE_SIZE
    page_size_query_param = "page_size"
