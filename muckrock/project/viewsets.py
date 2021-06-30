"""Viewsets for projects"""

# Third Party
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
