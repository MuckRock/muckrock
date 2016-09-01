"""
Provides Jurisdiction application API views
"""

from django.db.models import Q

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from muckrock.jurisdiction.forms import ExemptionSubmissionForm
from muckrock.jurisdiction.models import Jurisdiction, Exemption
from muckrock.jurisdiction.serializers import JurisdictionSerializer, ExemptionSerializer
from muckrock.task.models import NewExemptionTask

class JurisdictionViewSet(ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.select_related('parent__parent').order_by()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')


class ExemptionPermissions(DjangoModelPermissionsOrAnonReadOnly):
    """
    Allows authenticated users to submit exemptions.
    """
    def has_permission(self, request, view):
        """Allow authenticated users to submit exemptions."""
        if request.user.is_authenticated() and request.method in ['POST']:
            return True
        return super(ExemptionPermissions, self).has_permission(request, view)


class ExemptionViewSet(ModelViewSet):
    """
    The Exemption model provides a list of individual exemption cases along with some
    example appeal language.
    """
    queryset = (Exemption.objects.all().select_related('jurisdiction__parent__parent')
                                       .prefetch_related('example_appeals'))
    serializer_class = ExemptionSerializer
    filter_fields = ('name', 'jurisdiction')
    permission_classes = [ExemptionPermissions]

    def list(self, request):
        """
        Allows filtering against the collection of exemptions.
        Query is an optional filter.
        Jurisdiction is an optional filter.
        """
        results = self.queryset
        query = request.query_params.get('q')
        jurisdiction = request.query_params.get('jurisdiction')
        if query:
            results = self.queryset.filter(
                Q(name__icontains=query)|
                Q(basis__icontains=query)|
                Q(example_appeals__language__icontains=query)|
                Q(tags__name__icontains=query)
            ).distinct()
        if jurisdiction:
            results = results.filter(jurisdiction__pk=jurisdiction)
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        The exemption submission endpoint allows new exemptions to be submitted for staff review.
        When an exemption is submitted, we need to know the request it was invoked on and the
        language the agency used to invoke it. Then, we should create both an InvokedExemption
        and a NewExemptionTask.
        """
        # foia_id = request.data.get('foia')
        # language = request.data.get('language')
        form = ExemptionSubmissionForm(request.data)
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())
        foia = form.cleaned_data['foia']
        language = form.cleaned_data['language']
        task = NewExemptionTask.objects.create(
            foia=foia,
            language=language,
            user=request.user
        )
        return Response({})
