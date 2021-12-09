"""
Views for the Jurisdiction application
"""

# Django
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.db.models.expressions import Value
from django.db.models.fields import BooleanField
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView, TemplateView

# Third Party
from rest_framework import viewsets

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core.views import (
    MRAutocompleteView,
    MRFilterListView,
    MRSearchFilterListView,
)
from muckrock.crowdsource.models import Crowdsource
from muckrock.jurisdiction.filters import ExemptionFilterSet, JurisdictionFilterSet
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.models import Exemption, Jurisdiction
from muckrock.jurisdiction.serializers import JurisdictionSerializer
from muckrock.task.models import FlaggedTask


class JurisdictionExploreView(TemplateView):
    """An interactive map to explore different state laws"""

    template_name = "jurisdiction/explore.html"
    map_positions = {
        (5, 0): "USA",
        (0, 1): "AK",
        (10, 1): "ME",
        (9, 2): "VT",
        (10, 2): "NH",
        (0, 3): "WA",
        (1, 3): "ID",
        (2, 3): "MT",
        (3, 3): "ND",
        (4, 3): "MN",
        (6, 3): "MI",
        (8, 3): "NY",
        (9, 3): "MA",
        (10, 3): "RI",
        (0, 4): "OR",
        (1, 4): "UT",
        (2, 4): "WY",
        (3, 4): "SD",
        (4, 4): "IA",
        (5, 4): "WI",
        (6, 4): "IN",
        (7, 4): "OH",
        (8, 4): "PA",
        (9, 4): "NJ",
        (10, 4): "CT",
        (0, 5): "CA",
        (1, 5): "NV",
        (2, 5): "CO",
        (3, 5): "NE",
        (4, 5): "MO",
        (5, 5): "IL",
        (6, 5): "KY",
        (7, 5): "WV",
        (8, 5): "VA",
        (9, 5): "MD",
        (10, 5): "DE",
        (1, 6): "AZ",
        (2, 6): "NM",
        (3, 6): "KS",
        (4, 6): "AR",
        (5, 6): "TN",
        (6, 6): "NC",
        (7, 6): "SC",
        (8, 6): "DC",
        (3, 7): "OK",
        (4, 7): "LA",
        (5, 7): "MS",
        (6, 7): "AL",
        (7, 7): "GA",
        (0, 8): "HI",
        (3, 8): "TX",
        (8, 8): "FL",
    }

    def get_context_data(self, **kwargs):
        """Return the states and data for the map"""
        context = super(JurisdictionExploreView, self).get_context_data(**kwargs)
        states = {
            state.abbrev: state
            for state in Jurisdiction.objects.filter(level__in=["s", "f"])
            .select_related("law", "parent")
            .annotate(exemption_count=Count("exemptions"))
        }
        state_map = []
        for j in range(9):
            state_map.append([])
            for i in range(11):
                state_map[-1].append(states.get(self.map_positions.get((i, j))))
        context["state_map"] = state_map
        return context


@method_decorator(xframe_options_exempt, name="dispatch")
class JurisdictionEmbedView(JurisdictionExploreView):
    """View for embedding the map interactive"""

    template_name = "jurisdiction/embed.html"


def collect_stats(obj, context):
    """Helper for collecting stats"""
    statuses = ("rejected", "ack", "processed", "fix", "no_docs", "done", "appealing")
    requests = obj.get_requests()
    status_counts = (
        requests.filter(status__in=statuses)
        .order_by("status")
        .values_list("status")
        .annotate(Count("status"))
    )
    context.update({"num_%s" % s: c for s, c in status_counts})
    context["num_overdue"] = requests.get_overdue().count()
    context["num_submitted"] = requests.count()


def detail(request, fed_slug, state_slug=None, local_slug=None):
    """Details for a jurisdiction"""
    if local_slug:
        jurisdiction = get_object_or_404(
            Jurisdiction.objects.select_related("parent", "parent__parent"),
            level="l",
            slug=local_slug,
            parent__slug=state_slug,
            parent__parent__slug=fed_slug,
        )
    elif state_slug:
        jurisdiction = get_object_or_404(
            Jurisdiction.objects.select_related("parent"),
            level="s",
            slug=state_slug,
            parent__slug=fed_slug,
        )
    else:
        jurisdiction = get_object_or_404(Jurisdiction, level="f", slug=fed_slug)

    foia_requests = jurisdiction.get_requests()
    foia_requests = (
        foia_requests.get_public()
        .get_done()
        .order_by("-datetime_done")
        .select_related_view()
        .get_public_file_count(limit=10)[:10]
    )

    if jurisdiction.level == "s":
        agencies = Agency.objects.filter(
            Q(jurisdiction=jurisdiction) | Q(jurisdiction__parent=jurisdiction)
        ).select_related("jurisdiction")
    else:
        agencies = jurisdiction.agencies
    agencies = (
        agencies.get_approved()
        .only("pk", "slug", "name", "jurisdiction")
        .annotate(foia_count=Count("foiarequest", distinct=True))
        .annotate(pages=Sum("foiarequest__communications__files__pages"))
        .order_by("-foia_count")[:10]
    )

    _children = Jurisdiction.objects.filter(parent=jurisdiction).select_related(
        "parent__parent"
    )
    _top_children = (
        _children.annotate(foia_count=Count("agencies__foiarequest", distinct=True))
        .annotate(pages=Sum("agencies__foiarequest__communications__files__pages"))
        .order_by("-foia_count")[:10]
    )

    if request.method == "POST":
        form = FlagForm(request.POST)
        if form.is_valid() and request.user.is_authenticated:
            FlaggedTask.objects.create(
                user=request.user,
                text=form.cleaned_data.get("reason"),
                jurisdiction=jurisdiction,
            )
            messages.success(request, "We received your feedback. Thanks!")
            return redirect(jurisdiction)
    else:
        form = FlagForm()

    admin_url = reverse(
        "admin:jurisdiction_jurisdiction_change", args=(jurisdiction.pk,)
    )
    context = {
        "jurisdiction": jurisdiction,
        "agencies": agencies,
        "children": _children,
        "top_children": _top_children,
        "foia_requests": foia_requests,
        "form": form,
        "sidebar_admin_url": admin_url,
        "title": jurisdiction.name + " Public Records Guide",
    }
    if request.user.is_staff and jurisdiction.abbrev:
        context["proxies"] = User.objects.filter(
            profile__proxy=True, profile__state=jurisdiction.abbrev
        )
    collect_stats(jurisdiction, context)

    return render(request, "jurisdiction/detail.html", context)


class List(MRFilterListView):
    """Filterable list of jurisdictions"""

    model = Jurisdiction
    filter_class = JurisdictionFilterSet
    title = "Jurisdictions"
    template_name = "jurisdiction/list.html"
    default_sort = "name"
    sort_map = {"name": "name", "level": "level"}

    def get_queryset(self):
        """Hides hidden jurisdictions from list"""
        objects = super(List, self).get_queryset()
        objects = objects.exclude(hidden=True).select_related(
            "parent", "parent__parent"
        )
        return objects


def redirect_flag(request, **kwargs):
    """Redirect flag urls to base agency"""
    # pylint: disable=unused-argument
    # filter None from kwargs
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    return redirect("jurisdiction-detail", **kwargs)


class JurisdictionViewSet(viewsets.ModelViewSet):
    """API views for Jurisdiction"""

    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.select_related("parent__parent").order_by()
    serializer_class = JurisdictionSerializer
    filter_fields = ("name", "abbrev", "level", "parent")


class ExemptionDetailView(DetailView):
    """Detail view for an individual exemption"""

    model = Exemption
    template_name = "exemption/detail.html"

    def get_queryset(self):
        """Adds some database optimizations for getting the Exemption queryset."""
        _queryset = super(ExemptionDetailView, self).get_queryset()
        _queryset = _queryset.select_related(
            "jurisdiction__parent__parent"
        ).prefetch_related("requests", "requests__agency")
        return _queryset

    def get_context_data(self, **kwargs):
        """Adds a flag form to the context."""
        # crowdsource to link to on exemption pages
        crowdsource_pk = 20
        context = super(ExemptionDetailView, self).get_context_data(**kwargs)
        admin_url = reverse(
            "admin:jurisdiction_exemption_change", args=(self.object.pk,)
        )
        context["flag_form"] = FlagForm()
        context["sidebar_admin_url"] = admin_url
        context["federal_url"] = Jurisdiction.objects.get(level="f").get_absolute_url()
        assignment = Crowdsource.objects.filter(pk=crowdsource_pk).first()
        context["assignment_url"] = (
            reverse(
                "crowdsource-assignment",
                kwargs={"slug": assignment.slug, "idx": assignment.pk},
            )
            if assignment
            else "#"
        )
        context["contributors"] = self.object.contributors.select_related("profile")
        return context


class ExemptionListView(MRSearchFilterListView):
    """List view for exemptions"""

    model = Exemption
    title = "Exemptions"
    template_name = "jurisdiction/exemption_list.html"
    filter_class = ExemptionFilterSet
    default_sort = "name"
    sort_map = {"name": "name"}


class JurisdictionAutocomplete(MRAutocompleteView):
    """Autocomplete for jurisdictions"""

    queryset = Jurisdiction.objects.filter(hidden=False).order_by("-level", "name")
    search_fields = ["name", "abbrev", "parent__abbrev", "aliases"]
    split_words = "and"

    def get_queryset(self):
        """Extra filters"""
        # pylint: disable=attribute-defined-outside-init

        # treat commas as whitespace for splitting
        self.q = self.q.replace(",", " ")

        queryset = super().get_queryset()

        levels = self.forwarded.get("levels")
        if levels:
            queryset = queryset.filter(level__in=levels)

        return queryset


class JurisdictionStateInclusiveAutocomplete(JurisdictionAutocomplete):
    """Autocomplete containing state selections which include their localities"""

    template = "autocomplete/jurisdiction_inclusive.html"

    def get_result_value(self, result):
        """Value also must indicate if we are including localaties"""
        return f"{result.pk}-{result.include_local}"

    def get_queryset(self):
        """Union in state options with include local set to True"""

        queryset = super().get_queryset()

        queryset = (
            queryset.annotate(include_local=Value(False, output_field=BooleanField()))
            .union(
                queryset.filter(level="s").annotate(
                    include_local=Value(True, output_field=BooleanField())
                )
            )
            .order_by("-level", "name")
        )

        return queryset

    def get_selected_result_label(self, result):
        """Just text for selected result"""
        label = str(result)
        if result.include_local:
            label += " (include local)"
        return label
