"""Viewsets for projects"""

# Third Party
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

# MuckRock
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.project.api_v2.serializers import ProjectSerializer
from muckrock.project.models import Project


class ProjectViewSet(
    AuthenticatedAPIMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    API viewset for Projects
    """

    serializer_class = ProjectSerializer
    pagination_class = APIV2CursorPagination
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return Project.objects.get_viewable(self.request.user).prefetch_related(
            "contributors", "articles", "requests"
        )

    class Filter(django_filters.FilterSet):
        """API Filter for Projects"""

        contributors = django_filters.NumberFilter(
            field_name="contributors",
            help_text="User ID of a contributor on the project",
        )
        requests = django_filters.NumberFilter(
            field_name="requests",
            help_text="ID of a FOIA request attached to this project",
        )
        title = django_filters.CharFilter(
            field_name="title", lookup_expr="contains", help_text="Title of a project"
        )

        class Meta:
            model = Project
            fields = ["contributors", "requests", "title"]

    filterset_class = Filter
