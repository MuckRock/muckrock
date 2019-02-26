"""Viewsets for Agency"""

# Django
from django.db.models.aggregates import Avg, Count, Sum
from django.db.models.expressions import Case, F, Value, When
from django.db.models.fields import FloatField
from django.db.models.functions.base import Coalesce
from django.db.models.query import Prefetch

# Third Party
import django_filters
from rest_framework import viewsets

# MuckRock
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.core.models import ExtractDay, NullIf


class AgencyViewSet(viewsets.ModelViewSet):
    """API views for Agency"""
    # pylint: disable=too-many-public-methods
    queryset = (
        Agency.objects.order_by('id').select_related(
            'jurisdiction', 'parent', 'appeal_agency'
        ).prefetch_related(
            Prefetch(
                'emails',
                queryset=EmailAddress.objects.filter(
                    status='good',
                    agencyemail__request_type='primary',
                    agencyemail__email_type='to',
                ),
                to_attr='primary_emails',
            ),
            Prefetch(
                'phones',
                queryset=PhoneNumber.objects.filter(
                    type='fax',
                    status='good',
                    agencyphone__request_type='primary',
                ),
                to_attr='primary_faxes',
            ),
            Prefetch(
                'addresses',
                queryset=Address.objects.filter(
                    agencyaddress__request_type='primary',
                ),
                to_attr='primary_addresses',
            ),
            'types',
        ).annotate(
            average_response_time_=Coalesce(
                ExtractDay(
                    Avg(
                        F('foiarequest__datetime_done') -
                        F('foiarequest__composer__datetime_submitted')
                    )
                ), Value(0)
            ),
            fee_rate_=Coalesce(
                100 * Sum(
                    Case(
                        When(
                            foiarequest__price__gt=0,
                            then=1,
                        ),
                        default=0,
                    ),
                    output_field=FloatField()
                ) / NullIf(
                    Count('foiarequest'),
                    Value(0),
                    output_field=FloatField(),
                ), Value(0)
            ),
            success_rate_=Coalesce(
                100 * Sum(
                    Case(
                        When(
                            foiarequest__status__in=['done', 'partial'],
                            then=1,
                        ),
                        default=0,
                    ),
                    output_field=FloatField()
                ) / NullIf(
                    Count('foiarequest'),
                    Value(0),
                    output_field=FloatField(),
                ), Value(0)
            ),
        )
    )
    serializer_class = AgencySerializer
    # don't allow ordering by computed fields
    ordering_fields = [
        f for f in AgencySerializer.Meta.fields if f not in (
            'absolute_url',
            'average_response_time',
            'fee_rate',
            'success_rate',
        )
    ]

    def get_queryset(self):
        """Filter out non-approved agencies for non-staff"""
        if self.request.user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(status='approved')

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        types = django_filters.CharFilter(
            name='types__name',
            lookup_expr='iexact',
        )

        class Meta:
            model = Agency
            fields = (
                'name', 'status', 'jurisdiction', 'types', 'requires_proxy'
            )

    filter_class = Filter
