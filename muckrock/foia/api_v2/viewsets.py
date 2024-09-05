"""
Viewsets for V2 of the FOIA API
"""

# Django
from django.contrib.auth.models import User
from django.forms import widgets
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
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.project.models import Project


class FOIARequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """API for FOIA Requests"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    filter_backends = (DjangoFilterBackend,)

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

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Requests"""

        agency = django_filters.ModelChoiceFilter(
            queryset=Agency.objects.filter(status="approved"),
            widget=widgets.NumberInput(),
            help_text="Filter for requests from the given Agency ID",
        )
        embargo = django_filters.BooleanFilter(
            help_text="Filter for requests which do or do not have an embargo",
        )
        jurisdiction = django_filters.ModelChoiceFilter(
            queryset=Jurisdiction.objects.all(),
            field_name="agency__jurisdiction",
            widget=widgets.NumberInput(),
            label="Jurisdiction",
            help_text="Filter for requests from the given Jurisdiction ID",
        )
        project = django_filters.ModelChoiceFilter(
            queryset=Project.objects.all(),
            field_name="projects",
            widget=widgets.NumberInput(),
            label="Project",
            help_text="Filter for requests from the given Project ID",
        )
        tags = django_filters.CharFilter(
            field_name="tags__name",
            label="Tags",
            help_text="Filter by a given tag",
        )
        title = django_filters.CharFilter(help_text="Filter by the title")
        user = django_filters.ModelChoiceFilter(
            queryset=User.objects.all(),
            field_name="composer__user",
            widget=widgets.NumberInput(),
            label="User",
            help_text="Filter for requests from the given User ID",
        )

        order_by_field = "ordering"
        ordering = django_filters.OrderingFilter(
            fields=(
                ("composer__datetime_submitted", "datetime_submitted"),
                ("composer__user__username", "user"),
                ("agency__name", "agency"),
                ("datetime_done", "datetime_done"),
                ("datetime_updated", "datetime_updated"),
                ("title", "title"),
                ("status", "status"),
            )
        )

        class Meta:
            model = FOIARequest
            fields = (
                "agency",
                "embargo",
                "jurisdiction",
                "project",
                "status",
                "tags",
                "title",
                "user",
            )

    filterset_class = Filter


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
