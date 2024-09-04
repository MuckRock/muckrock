"""
Viewsets for V2 of the FOIA API
"""

# Django
from django.template.defaultfilters import slugify

# Third Party
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status as http_status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.foia.api_v2.serializers import (
    FOIACommunicationSerializer,
    FOIARequestCreateReturnSerializer,
    FOIARequestCreateSerializer,
    FOIARequestSerializer,
)
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.foia.models.composer import FOIAComposer


class FOIARequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """API for FOIA Requests"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    filter_backends = ()

    def get_serializer_class(self):
        if self.action == "create":
            return FOIARequestCreateSerializer

        return FOIARequestSerializer

    def get_queryset(self):
        return (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related("composer")
            .prefetch_related(
                "edit_collaborators", "read_collaborators", "tracking_ids"
            )
        )

    @extend_schema(
        responses={
            201: FOIARequestCreateReturnSerializer,
            402: FOIARequestCreateReturnSerializer,
        }
    )
    def create(self, request, *args, **kwargs):
        """File a new request"""

        composer = FOIAComposer.objects.create(
            user=request.user,
            organization_id=request.data.get(
                "organization", request.user.profile.organization.pk
            ),
            title=request.data["title"],
            slug=slugify(request.data["title"]) or "untitled",
            requested_docs=request.data["requested_docs"],
            embargo=request.data.get("embargo", False),
            permanent_embargo=request.data.get("permanent_embargo", False),
        )
        composer.agencies.set(Agency.objects.filter(pk__in=request.data["agencies"]))

        try:
            composer.submit()
        except InsufficientRequestsError:
            serializer = FOIARequestCreateReturnSerializer(
                data={
                    "status": "Out of requests.  FOI Request has been saved.",
                    "location": composer.get_absolute_url(),
                }
            )
            serializer.is_valid()
            return Response(
                serializer.data,
                status=http_status.HTTP_402_PAYMENT_REQUIRED,
            )
        else:
            serializer = FOIARequestCreateReturnSerializer(
                data={
                    "status": "FOI Request submitted",
                    "location": composer.get_absolute_url(),
                    "requests": [f.pk for f in composer.foias.all()],
                }
            )
            serializer.is_valid()
            return Response(
                serializer.data,
                status=http_status.HTTP_201_CREATED,
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
