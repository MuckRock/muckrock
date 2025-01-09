"""
Viewsets for V2 of the FOIA API
"""

# Django
from django.template.defaultfilters import slugify

# Third Party
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import filters, mixins, status as http_status, viewsets
from rest_framework.response import Response

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.foia.api_v2.serializers import (
    FOIACommunicationSerializer,
    FOIAFileSerializer,
    FOIARequestCreateSerializer,
    FOIARequestSerializer,
)
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.models import FOIACommunication, FOIAFile, FOIARequest
from muckrock.foia.models.composer import FOIAComposer


# pylint:disable=too-many-ancestors
class FOIARequestViewSet(
    AuthenticatedAPIMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """API for FOIA Requests"""

    # authentication_classes = [JWTAuthentication, SessionAuthentication]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)

    search_fields = ["title"]

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

    def create(self, request, *args, **kwargs):
        composer = FOIAComposer.objects.create(
            user=request.user,
            organization_id=request.data.get(
                "organization", request.user.profile.organization.pk
            ),
            title=request.data["title"],
            slug=slugify(request.data["title"]) or "untitled",
            requested_docs=request.data["requested_docs"],
            embargo_status=request.data.get("embargo_status", False),
        )
        composer.agencies.set(Agency.objects.filter(pk__in=request.data["agencies"]))

        try:
            composer.submit()
        except InsufficientRequestsError:
            return Response(
                {
                    "status": "Out of requests.  FOI Request has been saved.",
                    "location": composer.get_absolute_url(),
                },
                status=http_status.HTTP_402_PAYMENT_REQUIRED,
            )
        return Response(
            {
                "status": "FOI Request submitted",
                "location": composer.get_absolute_url(),
                "requests": [f.pk for f in composer.foias.all()],
            },
            status=http_status.HTTP_201_CREATED,
        )

    class Filter(django_filters.FilterSet):
        """Filters for requests"""

        agency = django_filters.NumberFilter(
            field_name="agency__id", label="ID of the agency the request was sent to."
        )
        jurisdiction = django_filters.NumberFilter(
            field_name="agency__jurisdiction__id",
            label="ID of the jurisdiction for the request.",
        )
        user = django_filters.NumberFilter(
            field_name="composer__user__id",
            label="ID of the user who sent the request.",
        )
        tags = django_filters.CharFilter(field_name="tags__name", label="Tags")

        title = django_filters.CharFilter(
            field_name="title", lookup_expr="icontains", label="Title of the request"
        )

        order_by_field = "ordering"
        ordering = django_filters.OrderingFilter(
            fields=(
                ("composer__datetime_submitted", "datetime_submitted"),
                ("composer__user__id", "user"),
                ("agency__id", "agency"),
                ("datetime_done", "datetime_done"),
                ("datetime_updated", "datetime_updated"),
                ("title", "title"),
                ("status", "status"),
            )
        )

        # pylint:disable=too-few-public-methods
        class Meta:
            """Filters"""

            model = FOIARequest
            fields = (
                "user",
                "title",
                "status",
                "embargo_status",
                "jurisdiction",
                "agency",
            )

    filterset_class = Filter


class FOIACommunicationViewSet(
    AuthenticatedAPIMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """API for FOIA Communications"""

    # authentication_classes = [JWTAuthentication, SessionAuthentication]
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

        response = django_filters.BooleanFilter(
            label="Indicates if the communication is a response"
        )

        # pylint:disable=too-few-public-methods
        class Meta:
            """Filters for foia communications"""

            model = FOIACommunication
            fields = ("max_date", "min_date", "foia", "status", "response")

    filterset_class = Filter


class FOIAFileViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API for managing FOIA files"""

    def get_queryset(self):
        return FOIAFile.objects.get_viewable(self.request.user)

    serializer_class = FOIAFileSerializer
    # authentication_classes = [JWTAuthentication, SessionAuthentication]

    filter_backends = (DjangoFilterBackend,)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA files"""

        communication = django_filters.NumberFilter(
            field_name="comm__id",
            label="Filter by the associated communication ID",
        )
        title = django_filters.CharFilter(
            field_name="title", lookup_expr="icontains", label="Filter by Title"
        )
        doc_id = django_filters.CharFilter(
            field_name="doc_id",
            lookup_expr="icontains",
            label="Filter by the unique slug for the file",
        )

        class Meta:
            """Filters for FOIA files"""

            model = FOIAFile
            fields = ("communication", "title", "doc_id")

    filterset_class = Filter
