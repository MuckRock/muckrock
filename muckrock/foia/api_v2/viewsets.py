"""
Viewsets for V2 of the FOIA API
"""

# Third Party
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

# MuckRock
from muckrock.foia.api_v2.serializers import (
    FOIACommunicationSerializer,
    FOIARequestSerializer,
)
from muckrock.foia.models import FOIACommunication, FOIARequest


class FOIARequestViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """API for FOIA Requests"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    serializer_class = FOIARequestSerializer
    filter_backends = ()

    def get_queryset(self):
        return (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related("composer")
            .prefetch_related(
                "edit_collaborators", "read_collaborators", "tracking_ids"
            )
        )


class FOIACommunicationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """API for FOIA Communications"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    serializer_class = FOIACommunicationSerializer
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        return FOIACommunication.objects.get_viewable(self.request.user)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Communications"""

        min_date = django_filters.DateFilter(
            field_name="datetime",
            lookup_expr="gte",
            label="Filter communications after this date",
        )
        max_date = django_filters.DateFilter(
            field_name="datetime",
            lookup_expr="lte",
            label="Filter communications before this date",
        )
        foia = django_filters.NumberFilter(
            field_name="foia__id", label="The ID of the associated request"
        )

        class Meta:
            model = FOIACommunication
            fields = ("max_date", "min_date", "foia", "status", "response")

    filterset_class = Filter
