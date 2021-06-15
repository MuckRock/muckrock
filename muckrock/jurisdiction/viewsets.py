"""
Provides Jurisdiction application API views
"""

# Django
from django.db.models import Q
from django.shortcuts import get_object_or_404

# Third Party
import django_filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# MuckRock
from muckrock.foia.models import FOIATemplate
from muckrock.jurisdiction.forms import ExemptionSubmissionForm
from muckrock.jurisdiction.models import Exemption, Jurisdiction
from muckrock.jurisdiction.serializers import (
    ExemptionSerializer,
    JurisdictionSerializer,
)
from muckrock.task.models import FlaggedTask
from muckrock.task.serializers import FlaggedTaskSerializer


class JurisdictionViewSet(ModelViewSet):
    """API views for Jurisdiction"""

    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.order_by("id").select_related("parent__parent")
    serializer_class = JurisdictionSerializer
    # don't allow ordering by computed fields
    ordering_fields = [
        f
        for f in JurisdictionSerializer.Meta.fields
        if f
        not in ("absolute_url", "average_response_time", "fee_rate", "success_rate")
    ]

    class Filter(django_filters.FilterSet):
        """API Filter for Jurisdictions"""

        parent = django_filters.NumberFilter(field_name="parent__id")

        class Meta:
            model = Jurisdiction
            fields = ("name", "abbrev", "level", "parent", "law__requires_proxy")

    filterset_class = Filter

    @action(detail=True)
    def template(self, request, pk=None):
        """API view to get the template language for a jurisdiction"""

        jurisdiction = get_object_or_404(Jurisdiction, pk=pk)

        text = FOIATemplate.objects.render(
            [], request.user, "<insert requested docs here>", jurisdiction=jurisdiction
        )

        return Response({"text": text})


class ExemptionPermissions(DjangoModelPermissionsOrAnonReadOnly):
    """
    Allows authenticated users to submit exemptions.
    """

    def has_permission(self, request, view):
        """Allow authenticated users to submit exemptions."""
        if request.user.is_authenticated and request.method in ["POST"]:
            return True
        return super(ExemptionPermissions, self).has_permission(request, view)


class ExemptionViewSet(ModelViewSet):
    """
    The Exemption model provides a list of individual exemption cases along with some
    example appeal language.
    """

    queryset = (
        Exemption.objects.order_by("id")
        .select_related("jurisdiction__parent__parent")
        .prefetch_related("example_appeals")
    )
    serializer_class = ExemptionSerializer
    permission_classes = [ExemptionPermissions]

    class Filter(django_filters.FilterSet):
        """API Filter for Examptions"""

        jurisdiction = django_filters.NumberFilter(field_name="jurisdiction__id")

        class Meta:
            model = Exemption
            fields = ("name", "jurisdiction")

    filter_class = Filter

    def list(self, request):
        """
        Allows filtering against the collection of exemptions.
        Query is an optional filter.
        Jurisdiction is an optional filter.
        """
        results = self.queryset
        query = request.query_params.get("q")
        jurisdiction = request.query_params.get("jurisdiction")
        if query:
            results = self.queryset.filter(
                Q(name__icontains=query)
                | Q(aliases__icontains=query)
                | Q(example_appeals__language__icontains=query)
                | Q(tags__name__icontains=query)
            ).distinct()
        if jurisdiction:
            results = results.filter(jurisdiction__pk=jurisdiction)
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def submit(self, request):
        """
        The exemption submission endpoint allows new exemptions to be submitted
        for staff review.  When an exemption is submitted, we need to know the
        request it was invoked on and the language the agency used to invoke it.
        Then, we should create both an InvokedExemption and a FlaggedTask.
        """
        form = ExemptionSubmissionForm(request.data)
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())
        foia = form.cleaned_data.get("foia")
        language = form.cleaned_data.get("language")
        task = FlaggedTask.objects.create(
            foia=foia, text=language, user=request.user, category="appeal"
        )
        return Response(FlaggedTaskSerializer(task).data)
