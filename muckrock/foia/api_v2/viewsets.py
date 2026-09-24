"""
Viewsets for V2 of the FOIA API
"""

# Django
from django.db import transaction
from django.db.models import Prefetch

# Third Party
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, mixins, status as http_status, viewsets
from rest_framework.response import Response

# MuckRock
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.foia.api_v2.serializers import (
    FOIACommunicationSerializer,
    FOIAFileSerializer,
    FOIARequestCreateResponseSerializer,
    FOIARequestCreateSerializer,
    FOIARequestDetailSerializer,
    FOIARequestSerializer,
)
from muckrock.foia.constants import BLOCKED_FROM_FILING_MESSAGE
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

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    pagination_class = APIV2CursorPagination

    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "create":
            return FOIARequestCreateSerializer
        if self.action == "retrieve":
            return FOIARequestDetailSerializer
        return FOIARequestSerializer

    def get_queryset(self):
        queryset = (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related("composer")
            .prefetch_related(
                "edit_collaborators", "read_collaborators", "tracking_ids", "tags"
            )
        )
        if self.action == "retrieve":
            # Load only the IDs of communications this user can see.
            # Communication bodies are large.
            viewable_communications = FOIACommunication.objects.get_viewable(
                self.request.user
            ).only("id", "foia_id")
            queryset = queryset.prefetch_related(
                Prefetch("communications", queryset=viewable_communications)
            )
        return queryset

    @extend_schema(
        request=FOIARequestCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=FOIARequestCreateResponseSerializer,
                description=(
                    "Request submitted. Returns the composer location and the "
                    "list of created FOIA request IDs."
                ),
            ),
            400: OpenApiResponse(
                description=(
                    "Validation failed. Possible causes: no valid agencies "
                    "provided, missing title or requested_docs, an organization "
                    "you are not a member of, or an embargo status you lack "
                    "permission to set."
                ),
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
            402: OpenApiResponse(
                response=FOIARequestCreateResponseSerializer,
                description=(
                    "The selected organization has no requests remaining. The "
                    "request has been saved as a draft; its location is returned."
                ),
            ),
            403: OpenApiResponse(
                description="This account has been blocked from filing new requests.",
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        """Submit a new request"""
        if request.user.profile.blocked_from_filing:
            return Response(
                {"status": BLOCKED_FROM_FILING_MESSAGE},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization = data.get("organization") or request.user.profile.organization

        with transaction.atomic():
            composer = FOIAComposer.objects.create(
                user=request.user,
                organization=organization,
                title=data["title"],
                requested_docs=data["requested_docs"],
                edited_boilerplate=data.get("edited_boilerplate", False),
                embargo_status=data.get("embargo_status", "public"),
            )
            composer.agencies.set(data["agencies"])

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
        else:
            foias = list(composer.foias.all())
            tags = data.get("tags", [])
            if tags:
                for foia in foias:
                    foia.tags.set(tags)
            return Response(
                {
                    "status": "FOI Request submitted",
                    "location": composer.get_absolute_url(),
                    "requests": [f.pk for f in foias],
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

        datetime_submitted__gte = django_filters.DateTimeFilter(
            field_name="composer__datetime_submitted",
            lookup_expr="gte",
            label="Requests submitted on or after this date",
        )
        datetime_submitted__lte = django_filters.DateTimeFilter(
            field_name="composer__datetime_submitted",
            lookup_expr="lte",
            label="Requests submitted on or before this date",
        )

        # pylint:disable=too-few-public-methods
        class Meta:
            """Filters"""

            model = FOIARequest
            fields = {
                "status": ["exact"],
                "embargo_status": ["exact"],
                "datetime_done": ["gte", "lte"],
                "datetime_updated": ["gte", "lte"],
            }

    filterset_class = Filter


class FOIACommunicationViewSet(
    AuthenticatedAPIMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """API for FOIA Communications"""

    serializer_class = FOIACommunicationSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = APIV2CursorPagination

    def get_queryset(self):
        # We show file IDs on this so for efficiency we need to prefetch
        # To avoid a query per communication.
        return FOIACommunication.objects.get_viewable(
            self.request.user
        ).prefetch_related("files")

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Communications"""

        # The datetime field is the date the communication was sent,
        # per the model. Not to be confused with python's datetime
        min_date = django_filters.DateFilter(
            field_name="datetime",
            lookup_expr="date__gte",
            label="Filter communications on or after this date",
        )
        max_date = django_filters.DateFilter(
            field_name="datetime",
            lookup_expr="date__lte",
            # Compare only its date part. A plain date is
            # otherwise treated as midnight, so max_date would drop everything
            # after 00:00 on that day.
            label="Filter communications on or before this date",
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
    pagination_class = APIV2CursorPagination
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
            lookup_expr="exact",
            label="Filter by the unique slug for the file",
        )

        class Meta:
            """Filters for FOIA files"""

            model = FOIAFile
            fields = ("communication", "title", "doc_id")

    filterset_class = Filter
