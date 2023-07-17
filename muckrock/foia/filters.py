"""
Filters for FOIA models
"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

# Standard Library
import re

# Third Party
import django_filters

# MuckRock
from muckrock.agency.models import Agency
from muckrock.communication.models import EmailAddress, PhoneNumber
from muckrock.core import autocomplete
from muckrock.core.filters import BLANK_STATUS, NULL_BOOLEAN_CHOICES, RangeWidget
from muckrock.foia.models import FOIARequest
from muckrock.project.models import Project
from muckrock.tags.models import Tag
from muckrock.task.constants import SNAIL_MAIL_CATEGORIES


class JurisdictionFilterSet(django_filters.FilterSet):
    """Mix in for including state inclusive jurisdiction filter"""

    jurisdiction = django_filters.CharFilter(
        widget=autocomplete.Select2MultipleSI(
            url="jurisdiction-state-inclusive-autocomplete",
            attrs={"data-placeholder": "Search jurisdictions", "data-html": True},
        ),
        method="filter_jurisdiction",
        label="Jurisdiction",
    )
    value_format = re.compile(r"\d+-(True|False)")
    jurisdiction_field = "agency__jurisdiction"

    def filter_jurisdiction(self, queryset, name, _value):
        """Filter jurisdction, allowing for state inclusive searches"""
        # pylint: disable=unused-argument
        values = self.request.GET.getlist("jurisdiction")
        query = Q()
        for value in values:
            if not self.value_format.match(value):
                continue
            pk, include_local = value.split("-")
            include_local = include_local == "True"
            query |= Q(**{"{}__pk".format(self.jurisdiction_field): pk})
            if include_local:
                query |= Q(**{"{}__parent__pk".format(self.jurisdiction_field): pk})
        return queryset.filter(query)


class FOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by status, agency, jurisdiction, user, or tags."""

    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    user = django_filters.ModelMultipleChoiceFilter(
        field_name="composer__user",
        label="User",
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users", "data-minimum-input-length": 2},
        ),
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        field_name="projects",
        queryset=lambda request: Project.objects.get_viewable(request.user),
        widget=autocomplete.ModelSelect2Multiple(
            url="project-autocomplete", attrs={"data-placeholder": "Search projects"}
        ),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__name",
        queryset=Tag.objects.all(),
        label="Tags",
        widget=autocomplete.ModelSelect2Multiple(
            url="tag-autocomplete", attrs={"data-placeholder": "Search tags"}
        ),
    )
    has_embargo = django_filters.BooleanFilter(
        field_name="embargo", widget=forms.Select(choices=NULL_BOOLEAN_CHOICES)
    )
    has_crowdfund = django_filters.BooleanFilter(
        field_name="crowdfund",
        label="Has Crowdfund",
        lookup_expr="isnull",
        exclude=True,
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    minimum_pages = django_filters.NumberFilter(
        field_name="communications__files__pages",
        lookup_expr="gte",
        label="Min. Pages",
        distinct=True,
        widget=forms.NumberInput(),
    )
    date_range = django_filters.DateFromToRangeFilter(
        field_name="communications__datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )
    file_types = django_filters.CharFilter(
        label="File Types", method="filter_file_types"
    )

    def filter_file_types(self, queryset, name, value):
        """Filter requests with certain types of files"""
        # pylint: disable=unused-argument
        file_types = value.split(",")
        query = Q()
        for file_type in file_types:
            query |= Q(communications__files__ffile__endswith=file_type.strip())
        return queryset.filter(query)

    class Meta:
        model = FOIARequest
        fields = ["status", "user", "agency", "jurisdiction", "projects"]


class MyFOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by status, agency, jurisdiction, or tags."""

    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__name",
        queryset=Tag.objects.all(),
        label="Tags",
        widget=autocomplete.ModelSelect2Multiple(
            url="tag-autocomplete", attrs={"data-placeholder": "Search tags"}
        ),
    )
    has_embargo = django_filters.BooleanFilter(
        field_name="embargo", widget=forms.Select(choices=NULL_BOOLEAN_CHOICES)
    )
    has_crowdfund = django_filters.BooleanFilter(
        field_name="crowdfund",
        lookup_expr="isnull",
        exclude=True,
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    minimum_pages = django_filters.NumberFilter(
        field_name="communications__files__pages",
        lookup_expr="gte",
        label="Min. Pages",
        distinct=True,
        widget=forms.NumberInput(),
    )
    date_range = django_filters.DateFromToRangeFilter(
        field_name="communications__datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )
    file_types = django_filters.CharFilter(
        label="File Types", method="filter_file_types"
    )

    def filter_file_types(self, queryset, name, value):
        """Filter requests with certain types of files"""
        # pylint: disable=unused-argument
        file_types = value.split(",")
        query = Q()
        for file_type in file_types:
            query |= Q(communications__files__ffile__endswith=file_type.strip())
        return queryset.filter(query)

    class Meta:
        model = FOIARequest
        fields = ["status", "agency", "jurisdiction"]


class ProcessingFOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by user, agency, jurisdiction, or tags."""

    user = django_filters.ModelMultipleChoiceFilter(
        field_name="composer__user",
        label="User",
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users", "data-minimum-input-length": 2},
        ),
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__name",
        queryset=Tag.objects.all(),
        label="Tags",
        widget=autocomplete.ModelSelect2Multiple(
            url="tag-autocomplete", attrs={"data-placeholder": "Search tags"}
        ),
    )

    class Meta:
        model = FOIARequest
        fields = ["user", "agency", "jurisdiction"]


class AgencyFOIARequestFilterSet(django_filters.FilterSet):
    """Filters for agency users"""

    user = django_filters.ModelMultipleChoiceFilter(
        field_name="composer__user",
        label="User",
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users", "data-minimum-input-length": 2},
        ),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__name",
        queryset=Tag.objects.all(),
        label="Tags",
        widget=autocomplete.ModelSelect2Multiple(
            url="tag-autocomplete", attrs={"data-placeholder": "Search tags"}
        ),
    )
    date_range = django_filters.DateFromToRangeFilter(
        field_name="communications__datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )

    class Meta:
        model = FOIARequest
        fields = ["user"]


class FOIACommunicationFilterSet(django_filters.FilterSet):
    """Filters for communications"""

    response = django_filters.BooleanFilter(
        field_name="response",
        label="Direction",
        widget=forms.Select(
            choices=[(None, "----------"), (True, "Inbound"), (False, "Outbound")]
        ),
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        field_name="foia__agency",
        label="Agency",
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    category = django_filters.ChoiceFilter(choices=SNAIL_MAIL_CATEGORIES)
    from_email = django_filters.ModelMultipleChoiceFilter(
        queryset=EmailAddress.objects.all(),
        field_name="emails__from_email",
        label="From Email",
        widget=autocomplete.ModelSelect2Multiple(
            url="email-autocomplete", attrs={"data-placeholder": "Search emails"}
        ),
    )
    to_email = django_filters.ModelMultipleChoiceFilter(
        queryset=EmailAddress.objects.all(),
        field_name="emails__to_emails",
        label="To Email",
        widget=autocomplete.ModelSelect2Multiple(
            url="email-autocomplete", attrs={"data-placeholder": "Search emails"}
        ),
    )
    fax = django_filters.ModelMultipleChoiceFilter(
        queryset=PhoneNumber.objects.filter(type="fax"),
        field_name="faxes__to_number",
        label="Fax Number",
        widget=autocomplete.ModelSelect2Multiple(
            url="fax-autocomplete", attrs={"data-placeholder": "Search fax numbers"}
        ),
    )

    type = django_filters.ChoiceFilter(
        label="Type",
        method="filter_type",
        choices=[
            ("emails", "Email"),
            ("faxes", "Fax"),
            ("mails", "Mail"),
            ("web_comms", "Web"),
            ("portals", "Portal"),
        ],
    )

    date_range = django_filters.DateFromToRangeFilter(
        field_name="datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )

    def filter_type(self, queryset, name, value):
        """Filter communications with certain types"""
        # pylint: disable=unused-argument
        if value is None:
            return queryset

        return queryset.exclude(**{value: None})


class FOIAFileFilterSet(django_filters.FilterSet):
    """Filters for files"""

    date_range = django_filters.DateFromToRangeFilter(
        field_name="datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )

class FOIALogFilterSet(django_filters.FilterSet):
    """Filters for files"""

    date_range = django_filters.DateFromToRangeFilter(
        field_name="date",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )
