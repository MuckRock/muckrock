"""Viewsets for projects"""

# Third Party
import django_filters
from rest_framework import mixins, viewsets

# MuckRock
from muckrock.project.models import Project
from muckrock.project.serializers import ProjectSerializer


class ProjectViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    API viewset for Projects
    """

    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.get_viewable(self.request.user).prefetch_related(
            "contributors", "articles", "requests"
        )

    class Filter(django_filters.FilterSet):
        """API Filter for Projects"""

        contributors = django_filters.NumberFilter(field_name="contributors")

        class Meta:
            model = Project
            fields = ["contributors"]

    filterset_class = Filter
