"""
Filters for the task application
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Third Party
import django_filters
from dal import forward

# MuckRock
from muckrock.agency.models import Agency
from muckrock.agency.viewsets import CountWhen
from muckrock.core import autocomplete
from muckrock.core.filters import BLANK_STATUS, BOOLEAN_CHOICES, RangeWidget
from muckrock.foia.filters import JurisdictionFilterSet
from muckrock.portal.models import PORTAL_TYPES
from muckrock.task.constants import (
    FLAG_CATEGORIES,
    PORTAL_CATEGORIES,
    SNAIL_MAIL_CATEGORIES,
)
from muckrock.task.models import (
    FlaggedTask,
    NewAgencyTask,
    PortalTask,
    ResponseTask,
    ReviewAgencyTask,
    SnailMailTask,
    Task,
)


class TaskFilterSet(django_filters.FilterSet):
    """Allows tasks to be filtered by whether they're resolved, and by who resolved them."""

    resolved = django_filters.BooleanFilter(
        label="Show Resolved", widget=forms.CheckboxInput()
    )
    resolved_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users"},
            forward=(forward.Const(True, "tasks"),),
        ),
    )
    assigned = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users"},
            forward=(forward.Const(True, "tasks"),),
        ),
    )
    deferred = django_filters.BooleanFilter(
        label="Deferred", method="filter_deferred", widget=forms.CheckboxInput()
    )
    date_created = django_filters.DateFromToRangeFilter(
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )

    class Meta:
        model = Task
        fields = ["resolved", "resolved_by"]

    def filter_deferred(self, queryset, name, value):
        """Check if the foia has a tracking number."""
        # pylint: disable=unused-argument
        if value:
            queryset = queryset.get_deferred()
        else:
            queryset = queryset.get_undeferred()
        return queryset


class ResponseTaskFilterSet(TaskFilterSet):
    """Allows response tasks to be filtered by predicted status."""

    predicted_status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    scan = django_filters.BooleanFilter(label="Scans")

    class Meta:
        model = ResponseTask
        fields = ["predicted_status", "scan", "resolved", "resolved_by"]


class NewAgencyTaskFilterSet(TaskFilterSet):
    """Allows new agency tasks to be filtered by jurisdiction."""

    class Meta:
        model = NewAgencyTask
        fields = ["agency__jurisdiction__level", "resolved", "resolved_by"]


class SnailMailTaskFilterSet(TaskFilterSet):
    """Allows snail mail tasks to be filtered by category, as well as the
    presence of a tracking number or an agency note."""

    category = django_filters.ChoiceFilter(
        choices=[("", "All")] + SNAIL_MAIL_CATEGORIES
    )
    has_address = django_filters.ChoiceFilter(
        method="filter_has_address", label="Has address", choices=BOOLEAN_CHOICES
    )
    has_attachments = django_filters.ChoiceFilter(
        method="filter_has_attachments",
        label="Has attachments",
        choices=BOOLEAN_CHOICES,
    )
    has_tracking_number = django_filters.ChoiceFilter(
        method="filter_has_tracking_number",
        label="Has tracking number",
        choices=BOOLEAN_CHOICES,
    )
    has_agency_notes = django_filters.ChoiceFilter(
        method="filter_has_agency_notes",
        label="Has agency notes",
        choices=BOOLEAN_CHOICES,
    )
    resolved = django_filters.BooleanFilter(
        label="Show Resolved", widget=forms.CheckboxInput()
    )
    resolved_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users"},
            forward=(forward.Const(True, "tasks"),),
        ),
    )

    def blank_choice(self, queryset, name, value):
        """Check if the value is blank"""
        if value == "True":
            return queryset.exclude(**{name: ""})
        elif value == "False":
            return queryset.filter(**{name: ""})
        return queryset

    def filter_has_address(self, queryset, name, value):
        """Check if the foia has an address."""
        # pylint: disable=unused-argument
        if value == "True":
            return queryset.exclude(communication__foia__address=None)
        else:
            return queryset.filter(communication__foia__address=None)

    def filter_has_attachments(self, queryset, name, value):
        """Check if the communication has attachments."""
        # pylint: disable=unused-argument
        if value == "True":
            return queryset.exclude(communication__files=None)
        else:
            return queryset.filter(communication__files=None)

    def filter_has_tracking_number(self, queryset, name, value):
        """Check if the foia has a tracking number."""
        # pylint: disable=unused-argument
        if value == "True":
            return queryset.exclude(communication__foia__tracking_ids=None)
        else:
            return queryset.filter(communication__foia__tracking_ids=None)

    def filter_has_agency_notes(self, queryset, name, value):
        """Check if the agency has notes."""
        # pylint: disable=unused-argument
        return self.blank_choice(queryset, "communication__foia__agency__notes", value)

    class Meta:
        model = SnailMailTask
        fields = [
            "category",
            "has_address",
            "has_attachments",
            "has_tracking_number",
            "has_agency_notes",
            "resolved",
            "resolved_by",
        ]


class FlaggedTaskFilterSet(TaskFilterSet):
    """Allows a flagged task to be filtered by a user."""

    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users", "data-minimum-input-length": 2},
        ),
    )
    category = django_filters.ChoiceFilter(choices=FLAG_CATEGORIES)

    class Meta:
        model = FlaggedTask
        fields = ["user", "category", "resolved", "resolved_by"]


class ReviewAgencyTaskFilterSet(JurisdictionFilterSet, TaskFilterSet):
    """Allows a review agency task to be filtered by jurisdiction."""

    COMPLICATED_LIMIT = 10

    jurisdiction_field = "agency__jurisdiction"

    agency = django_filters.ModelMultipleChoiceFilter(
        field_name="agency",
        queryset=Agency.objects.exclude(reviewagencytask=None),
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )

    federal = django_filters.ChoiceFilter(
        method="filter_federal", label="Federal Agencies", choices=BOOLEAN_CHOICES
    )

    complicated = django_filters.ChoiceFilter(
        method="filter_complicated", label="Complicated Tasks", choices=BOOLEAN_CHOICES
    )

    source = django_filters.ChoiceFilter(choices=ReviewAgencyTask.sources)

    class Meta:
        model = ReviewAgencyTask
        fields = ["jurisdiction", "agency", "resolved", "resolved_by"]

    def filter_federal(self, queryset, name, value):
        """Check if the task is for a federal agency"""
        # pylint: disable=unused-argument
        if value == "True":
            return queryset.filter(agency__jurisdiction__level="f")
        else:
            return queryset.exclude(agency__jurisdiction__level="f")

    def filter_complicated(self, queryset, name, value):
        """Check if the task is for a federal agency"""
        # pylint: disable=unused-argument
        queryset = queryset.annotate(
            c=CountWhen(
                agency__foiarequest__status__in=["ack", "processed", "appealing"]
            )
        )
        if value == "True":
            return queryset.filter(c__gte=self.COMPLICATED_LIMIT)
        else:
            return queryset.exclude(c__gte=self.COMPLICATED_LIMIT)


class PortalTaskFilterSet(TaskFilterSet):
    """Allows portal tasks to be filtered by category"""

    # pylint: disable=invalid-name
    category = django_filters.ChoiceFilter(choices=PORTAL_CATEGORIES)
    agency = django_filters.ModelMultipleChoiceFilter(
        field_name="communication__foia__agency",
        label="Agency",
        queryset=Agency.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete", attrs={"data-placeholder": "Search agencies"}
        ),
    )
    communication__foia__portal__type = django_filters.ChoiceFilter(
        choices=PORTAL_TYPES, label="Portal Type"
    )
    resolved = django_filters.BooleanFilter(
        label="Show Resolved", widget=forms.CheckboxInput()
    )
    resolved_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search users"},
            forward=(forward.Const(True, "tasks"),),
        ),
    )

    class Meta:
        model = PortalTask
        fields = [
            "category",
            "agency",
            "communication__foia__portal__type",
            "resolved",
            "resolved_by",
        ]
