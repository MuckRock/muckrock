"""Viewsets for Agency"""

# Django
from django.db.models.aggregates import Avg, Count, Sum
from django.db.models.expressions import Case, F, Value, When
from django.db.models.fields import FloatField, IntegerField
from django.db.models.functions import Coalesce
from django.db.models.query import Prefetch

# Third Party
import django_filters
from rest_framework import viewsets

# MuckRock
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.core.models import ExtractDay, NullIf


def CountWhen(output_field=None, **kwargs):
    """Use Sum-Case to simulate a filtered Count"""
    # pylint: disable=invalid-name
    if output_field is None:
        output_field = IntegerField()
    return Sum(Case(When(then=1, **kwargs), default=0), output_field=output_field)


class AgencyViewSet(viewsets.ModelViewSet):
    """API views for Agency"""

    # pylint: disable=too-many-public-methods
    queryset = (
        Agency.objects.order_by("id")
        .select_related("jurisdiction", "parent", "appeal_agency")
        .prefetch_related(
            "agencyemail_set__email",
            "agencyphone_set__phone",
            "agencyaddress_set__address",
            Prefetch(
                "emails",
                queryset=EmailAddress.objects.filter(
                    status="good",
                    agencyemail__request_type="primary",
                    agencyemail__email_type="to",
                ),
                to_attr="primary_emails",
            ),
            Prefetch(
                "phones",
                queryset=PhoneNumber.objects.filter(
                    type="fax", status="good", agencyphone__request_type="primary"
                ),
                to_attr="primary_faxes",
            ),
            Prefetch(
                "addresses",
                queryset=Address.objects.filter(agencyaddress__request_type="primary"),
                to_attr="primary_addresses",
            ),
            "types",
        )
        .annotate(
            average_response_time_=Coalesce(
                ExtractDay(
                    Avg(
                        F("foiarequest__datetime_done")
                        - F("foiarequest__composer__datetime_submitted")
                    )
                ),
                Value(0),
            ),
            fee_rate_=Coalesce(
                100
                * CountWhen(foiarequest__price__gt=0, output_field=FloatField())
                / NullIf(Count("foiarequest"), Value(0), output_field=FloatField()),
                Value(0),
                output_field=FloatField(),
            ),
            success_rate_=Coalesce(
                100
                * CountWhen(
                    foiarequest__status__in=["done", "partial"],
                    output_field=FloatField(),
                )
                / NullIf(Count("foiarequest"), Value(0), output_field=FloatField()),
                Value(0),
                output_field=FloatField(),
            ),
            number_requests=Count("foiarequest"),
            number_requests_completed=CountWhen(foiarequest__status="done"),
            number_requests_rejected=CountWhen(foiarequest__status="rejected"),
            number_requests_no_docs=CountWhen(foiarequest__status="no_docs"),
            number_requests_ack=CountWhen(foiarequest__status="ack"),
            number_requests_resp=CountWhen(foiarequest__status="processed"),
            number_requests_fix=CountWhen(foiarequest__status="fix"),
            number_requests_appeal=CountWhen(foiarequest__status="appealing"),
            number_requests_pay=CountWhen(foiarequest__status="payment"),
            number_requests_partial=CountWhen(foiarequest__status="partial"),
            number_requests_lawsuit=CountWhen(foiarequest__status="lawsuit"),
            number_requests_withdrawn=CountWhen(foiarequest__status="abandoned"),
        )
    )
    serializer_class = AgencySerializer
    # don't allow ordering by computed fields
    ordering_fields = [
        f
        for f in AgencySerializer.Meta.fields
        if f
        not in ("absolute_url", "average_response_time", "fee_rate", "success_rate")
        and not f.startswith(("has_", "number_"))
    ]

    def get_queryset(self):
        """Filter out non-approved agencies for non-staff"""
        if self.request.user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(status="approved")

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""

        jurisdiction = django_filters.NumberFilter(field_name="jurisdiction__id")
        types = django_filters.CharFilter(
            field_name="types__name", lookup_expr="iexact"
        )

        class Meta:
            model = Agency
            fields = ("name", "status", "jurisdiction", "types", "requires_proxy")

    filterset_class = Filter
