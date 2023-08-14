"""
Views to display lists of FOIA requests
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Prefetch
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

# Standard Library
from datetime import date, timedelta

# Third Party
import actstream
from actstream.models import following
from furl import furl

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core.forms import TagManagerForm
from muckrock.core.views import MRListView, MRSearchFilterListView, class_view_decorator
from muckrock.crowdsource.forms import CrowdsourceChoiceForm
from muckrock.crowdsource.tasks import datum_per_page
from muckrock.foia.filters import (
    AgencyFOIARequestFilterSet,
    FOIARequestFilterSet,
    MyFOIARequestFilterSet,
    ProcessingFOIARequestFilterSet,
)
from muckrock.foia.forms import (
    FOIAAccessForm,
    FOIAOwnerForm,
    SaveSearchForm,
    SaveSearchFormHandler,
)
from muckrock.foia.models import (
    END_STATUS,
    FOIACommunication,
    FOIAComposer,
    FOIARequest,
    FOIASavedSearch,
)
from muckrock.foia.rules import can_embargo, can_embargo_permananently
from muckrock.foia.tasks import export_csv, noindex_documentcloud
from muckrock.news.models import Article
from muckrock.project.forms import ProjectManagerForm
from muckrock.project.models import Project
from muckrock.tags.models import Tag, normalize
from muckrock.task.models import (
    MultiRequestTask,
    NewAgencyTask,
    PaymentInfoTask,
    PortalTask,
    ReviewAgencyTask,
    SnailMailTask,
)


class RequestExploreView(TemplateView):
    """Provides a top-level page for exploring interesting requests."""

    template_name = "foia/explore.html"

    def get_context_data(self, **kwargs):
        """Adds interesting data to the context for rendering."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        visible_requests = FOIARequest.objects.get_viewable(user)
        context["top_agencies"] = (
            Agency.objects.get_approved()
            .annotate(foia_count=Count("foiarequest"))
            .order_by("-foia_count")
        )[:9]
        context["featured_requests"] = (
            visible_requests.filter(featured=True)
            .order_by("featured")
            .select_related_view()
        )
        context["recent_news"] = (
            Article.objects.get_published()
            .annotate(foia_count=Count("foias"))
            .exclude(foia_count__lt=2)
            .exclude(foia_count__gt=9)
            .prefetch_related(
                "authors",
                Prefetch(
                    "foias",
                    queryset=FOIARequest.objects.select_related(
                        "composer__user", "agency__jurisdiction__parent__parent"
                    ),
                ),
            )
            .order_by("-pub_date")
        )[:3]
        context["featured_projects"] = (
            Project.objects.get_viewable(user)
            .filter(featured=True)
            .prefetch_related(
                Prefetch(
                    "requests",
                    queryset=FOIARequest.objects.select_related(
                        "composer__user", "agency__jurisdiction__parent__parent"
                    ),
                )
            )
        )
        context["recently_completed"] = (
            visible_requests.get_done()
            .order_by("-datetime_done")
            .select_related_view()
            .get_public_file_count(limit=5)
        )
        context["recently_rejected"] = (
            visible_requests.filter(status__in=["rejected", "no_docs"])
            .order_by("-datetime_updated")
            .select_related_view()
            .get_public_file_count(limit=5)
        )
        return context


class RequestList(MRSearchFilterListView):
    """Base list view for other list views to inherit from"""

    model = FOIARequest
    filter_class = FOIARequestFilterSet
    title = "All Requests"
    template_name = "foia/list.html"
    default_sort = "datetime_updated"
    default_order = "desc"
    sort_map = {
        "title": "title",
        "user": "composer__user__profile__full_name",
        "agency": "agency__name",
        "date_updated": "datetime_updated",
        "date_submitted": "composer__datetime_submitted",
        "date_done": "datetime_done",
    }

    def get_queryset(self):
        """Limits requests to those visible by current user"""
        objects = super().get_queryset()
        objects = (
            objects.select_related(
                "agency__jurisdiction__parent", "composer__user__profile"
            )
            .only(
                "title",
                "slug",
                "status",
                "embargo",
                "datetime_updated",
                "agency__name",
                "agency__jurisdiction__name",
                "agency__jurisdiction__slug",
                "agency__jurisdiction__level",
                "agency__jurisdiction__parent__abbrev",
                "composer__user__profile__full_name",
                "composer__datetime_submitted",
                "crowdfund_id",
            )
            .prefetch_related("crowdfund")
        )
        return objects.get_viewable(self.request.user)

    def get_context_data(self, **kwargs):
        """Add download link for downloading csv"""
        context = super().get_context_data(**kwargs)
        url = furl(self.request.get_full_path())
        url.args["content_type"] = "csv"
        context["csv_link"] = url.url
        context["save_search_form"] = SaveSearchForm(
            initial={"search_title": self.request.GET.get("search_title")}
        )
        if self.request.user.is_authenticated:
            context["crowdsource_form"] = CrowdsourceChoiceForm(user=self.request.user)
            context["saved_searches"] = FOIASavedSearch.objects.filter(
                user=self.request.user
            )
        if self.request.user.is_staff:
            context["owner_form"] = FOIAOwnerForm(required=False)
        return context

    def render_to_response(self, context, **kwargs):
        """Allow CSV responses"""

        wants_csv = self.request.GET.get("content_type") == "csv"
        has_perm = self.request.user.has_perm("foia.export_csv")
        if wants_csv and has_perm:
            export_csv.delay(
                list(context["paginator"].object_list.values_list("pk", flat=True)),
                self.request.user.pk,
            )
            messages.info(
                self.request,
                "Your CSV is being processed.  It will be emailed to you when "
                "it is ready.",
            )

        return super().render_to_response(context, **kwargs)

    def post(self, request, *args, **kwargs):
        """Allow saving a search/filter"""
        actions = self.get_actions()

        if request.user.is_anonymous:
            messages.error(request, "Please log in")
            return redirect(request.resolver_match.view_name)

        if "delete" in request.POST:
            return self._delete(request)

        if request.POST.get("action") == "save":
            return self._save_search(request)

        try:
            foias = FOIARequest.objects.filter(pk__in=request.POST.getlist("foias"))
            msg = actions[request.POST["action"]](foias, request.user, request.POST)
            if msg:
                messages.success(request, msg)
        except (KeyError, ValueError):
            if request.POST.get("action") != "":
                messages.error(request, "Something went wrong")

        return redirect(
            "{}?{}".format(
                reverse(request.resolver_match.view_name), request.GET.urlencode()
            )
        )

    def get_actions(self):
        """Get available actions for this view"""
        actions = {
            "follow": self._follow,
            "unfollow": self._unfollow,
            "crowdsource": self._crowdsource,
            "crowdsource_page": self._crowdsource_page,
        }
        if self.request.user.is_staff:
            actions["review-agency"] = self._review_agency
            actions["change-owner"] = self._change_owner
            actions["embargo"] = self._embargo
            actions["noindex"] = self._noindex
        return actions

    def _delete(self, request):
        """Delete a saved search"""
        try:
            search = FOIASavedSearch.objects.get(
                pk=request.POST.get("delete"), user=request.user
            )
            search.delete()
            messages.success(request, "The saved search was deleted")
        except FOIASavedSearch.DoesNotExist:
            messages.error(request, "That saved search no longer exists")
        return redirect(request.resolver_match.view_name)

    def _save_search(self, request):
        """Save a search"""
        form_handler = SaveSearchFormHandler(request, self.filter_class)
        if form_handler.is_valid():
            search = form_handler.create_saved_search()
            messages.success(request, "Search saved")
            return redirect(
                "{}?{}".format(
                    reverse(request.resolver_match.view_name), search.urlencode()
                )
            )
        else:
            return redirect(request.resolver_match.view_name)

    def _follow(self, foias, user, _post):
        """Follow the selected requests"""
        foias = foias.get_viewable(user)
        for foia in foias:
            actstream.actions.follow(user, foia, actor_only=False)
        return "Followed requests"

    def _unfollow(self, foias, user, _post):
        """Unfollow the selected requests"""
        foias = foias.get_viewable(user)
        for foia in foias:
            actstream.actions.unfollow(user, foia)
        return "Unfollowed requests"

    def _crowdsource(self, foias, user, post):
        """Add the files to the crowdsource"""
        self._crowdsource_base(foias, user, post, split=False)

    def _crowdsource_page(self, foias, user, post):
        """Add the files to the crowdsource, split per page"""
        self._crowdsource_base(foias, user, post, split=True)

    def _crowdsource_base(self, foias, user, post, split):
        """Helper function for both crowdsource actions"""
        foias = foias.prefetch_related("communications__files")
        foias = [f for f in foias if f.has_perm(user, "view")]
        form = CrowdsourceChoiceForm(post, user=user)
        if form.is_valid():
            crowdsource = form.cleaned_data["crowdsource"]
            if crowdsource is None:
                return "No crowdsource selected"
            for foia in foias:
                for comm in foia.communications.all():
                    for file_ in comm.files.all():
                        if file_.doc_id and split:
                            datum_per_page.delay(crowdsource.pk, file_.doc_id, {})
                        elif file_.doc_id and not split:
                            crowdsource.data.create(
                                url="https://beta.documentcloud.org/documents/"
                                f"{file_.doc_id}/"
                            )
        return "Files added to assignment"

    def _review_agency(self, foias, user, _post):
        """Open review agency tasks for the selected foia's agencies"""
        foias = foias.get_viewable(user)
        for foia in foias:
            ReviewAgencyTask.objects.ensure_one_created(
                agency=foia.agency, resolved=False, source="staff"
            )
        return "Review agency tasks created"

    def _change_owner(self, foias, user, post):
        """Change the owner of the request"""
        form = FOIAOwnerForm(post)
        if form.is_valid():
            form.change_owner(user, foias)
            new_user = form.cleaned_data["user"]
            return (
                "Requests have been succesfully transferred to "
                f"{new_user.profile.full_name} ({new_user.username})"
            )
        else:
            return None

    def _embargo(self, foias, _user, _post):
        """Embargo the requests"""
        foias.update(embargo=True, permanent_embargo=True)
        return "Requests have been embargoed"

    def _noindex(self, foias, _user, _post):
        """No index the requests"""
        with transaction.atomic():
            foias.update(noindex=True)
            for foia in foias:
                transaction.on_commit(lambda f=foia: noindex_documentcloud.delay(f.pk))
        return "Requests have been no-indexed"

    def get(self, request, *args, **kwargs):
        """Check for loading saved searches"""
        if "load" in request.GET and request.user.is_authenticated:
            try:
                search = FOIASavedSearch.objects.get(
                    title=request.GET.get("load"), user=request.user
                )
            except FOIASavedSearch.DoesNotExist:
                return super().get(request, *args, **kwargs)
            return redirect(
                "{}?{}".format(
                    reverse(request.resolver_match.view_name), search.urlencode()
                )
            )
        else:
            return super().get(request, *args, **kwargs)


@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""

    filter_class = MyFOIARequestFilterSet
    title = "Your Requests"
    template_name = "foia/my_list.html"

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super().get_queryset()
        return queryset.filter(composer__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add forms for bulk actions"""
        context = super().get_context_data(**kwargs)
        context["project_form"] = ProjectManagerForm(user=self.request.user)
        # set auto_id to avoid clashing IDs with the tag filter
        context["tag_form"] = TagManagerForm(required=False, auto_id="id_tm_%s")
        context["share_form"] = FOIAAccessForm(required=False)
        context["can_embargo"] = can_embargo(self.request.user)
        context["can_perm_embargo"] = can_embargo_permananently(self.request.user)
        context["owner_form"] = FOIAOwnerForm(required=False)
        return context

    def get_actions(self):
        """Get available actions for this view"""
        actions = super().get_actions()
        actions.update(
            {
                "extend-embargo": self._extend_embargo,
                "remove-embargo": self._remove_embargo,
                "permanent-embargo": self._perm_embargo,
                "project": self._project,
                "tags": self._tags,
                "share": self._share,
                "change-owner": self._change_owner,
                "autofollowup-on": self._autofollowup_on,
                "autofollowup-off": self._autofollowup_off,
            }
        )
        return actions

    def _extend_embargo(self, foias, user, _post):
        """Extend the embargo on the selected requests"""
        end_date = date.today() + timedelta(30)
        foias = [f.pk for f in foias if f.has_perm(user, "embargo")]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=True)
        # only set date if in end state
        FOIARequest.objects.filter(pk__in=foias, status__in=END_STATUS).update(
            date_embargo=end_date
        )
        return "Embargoes extended for 30 days"

    def _remove_embargo(self, foias, user, _post):
        """Remove the embargo on the selected requests"""
        foias = [f.pk for f in foias if f.has_perm(user, "embargo")]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=False)
        return "Embargoes removed"

    def _perm_embargo(self, foias, user, _post):
        """Permanently embargo the selected requests"""
        foias = [f.pk for f in foias if f.has_perm(user, "embargo_perm")]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=True)
        # only set permanent
        FOIARequest.objects.filter(pk__in=foias, status__in=END_STATUS).update(
            permanent_embargo=True
        )
        return "Embargoes extended permanently"

    def _project(self, foias, user, post):
        """Add the requests to the selected projects"""
        foias = [f for f in foias if f.has_perm(user, "change")]
        form = ProjectManagerForm(post, user=user)
        if form.is_valid():
            projects = form.cleaned_data["projects"]
            for foia in foias:
                foia.projects.add(*projects)
            return "Requests added to projects"
        else:
            return None

    def _tags(self, foias, user, post):
        """Add tags to the selected requests"""
        foias = [f for f in foias if f.has_perm(user, "change")]
        tags = [
            Tag.objects.get_or_create(name=normalize(t)) for t in post.getlist("tags")
        ]
        tags = {t for t, _ in tags}
        for foia in foias:
            foia.tags.add(*tags)
        return "Tags added to requests"

    def _share(self, foias, user, post):
        """Share the requests with the selected users"""
        foias = [f for f in foias if f.has_perm(user, "change")]
        form = FOIAAccessForm(post)
        if form.is_valid():
            access = form.cleaned_data["access"]
            users = form.cleaned_data["users"]
            if access == "edit":
                for foia in foias:
                    foia.read_collaborators.remove(*users)
                    foia.edit_collaborators.add(*users)
            elif access == "view":
                for foia in foias:
                    foia.edit_collaborators.remove(*users)
                    foia.read_collaborators.add(*users)
            return "Requests shared"
        else:
            return None

    def _autofollowup_on(self, foias, user, _post):
        """Turn autofollowups on"""
        return self._autofollowup(foias, user, disable=False)

    def _autofollowup_off(self, foias, user, _post):
        """Turn autofollowups off"""
        return self._autofollowup(foias, user, disable=True)

    def _autofollowup(self, foias, user, disable):
        """Set autofollowups"""
        foias = [f.pk for f in foias if f.has_perm(user, "change")]
        FOIARequest.objects.filter(pk__in=foias).update(disable_autofollowups=disable)
        action = "disabled" if disable else "enabled"
        return "Autofollowups {}".format(action)


class MyOrgRequestList(UserPassesTestMixin, RequestList):
    """View requests owned by current user's organization"""

    filter_class = FOIARequestFilterSet
    title = "Organization Requests"
    template_name = "foia/list.html"

    def test_func(self):
        """User must have a non-individual org"""
        user = self.request.user
        return user.is_authenticated and not user.profile.organization.individual

    def get_queryset(self):
        """Limit to just requests owned by the current organization."""
        queryset = super().get_queryset()
        return queryset.filter(
            composer__organization=self.request.user.profile.organization
        )


class MyProxyRequestList(UserPassesTestMixin, RequestList):
    """View requests that you are the proxy for"""

    filter_class = FOIARequestFilterSet
    title = "My Proxy Requests"
    template_name = "foia/list.html"

    def test_func(self):
        """User must be a proxy"""
        return self.request.user.profile.proxy

    def get_queryset(self):
        """Limit to just requests the user is a proxy for"""
        return super().get_queryset().filter(proxy=self.request.user)


@class_view_decorator(
    user_passes_test(lambda u: u.is_authenticated and u.profile.is_agency_user)
)
class AgencyRequestList(RequestList):
    """View requests owned by current agency"""

    filter_class = AgencyFOIARequestFilterSet
    title = "Your Agency's Requests"
    template_name = "foia/agency_list.html"

    def get_queryset(self):
        """Requests owned by the current agency that they can respond to."""
        queryset = super().get_queryset()
        return queryset.filter(
            agency=self.request.user.profile.agency,
            status__in=("ack", "processed", "appealing", "fix", "payment", "partial"),
        )


@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""

    title = "Requests You Follow"

    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        queryset = super().get_queryset()
        followed = [
            f.pk for f in following(self.request.user, FOIARequest) if f is not None
        ]
        return queryset.filter(pk__in=followed)


class BaseProcessingRequestList(RequestList):
    """List all of the currently processing FOIA requests."""

    filter_class = ProcessingFOIARequestFilterSet
    template_name = "foia/processing_list.html"
    default_sort = "date_processing"
    default_order = "asc"
    sort_map = {
        "title": "title",
        "date_submitted": "composer__datetime_submitted",
        "date_processing": "date_processing",
    }

    def dispatch(self, *args, **kwargs):
        """Only staff can see the list of processing requests."""
        if not self.request.user.is_staff:
            raise Http404()
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        """Apply select and prefetch related"""

        def make_prefetch(task):
            """
            Make a Prefetch object to get tasks from the communications for
            the request
            """
            name = task.__name__.lower()
            return Prefetch(
                "communications",
                queryset=FOIACommunication.objects.filter(
                    **{f"{name}__resolved": False}
                ).prefetch_related(
                    Prefetch(
                        f"{name}_set",
                        queryset=task.objects.filter(resolved=False),
                        to_attr=f"open_{name}s",
                    ),
                ),
                to_attr=f"{name}_communications",
            )

        objects = super().get_queryset()
        objects = (
            objects.only(
                "title",
                "slug",
                "status",
                "agency__name",
                "agency__jurisdiction__name",
                "agency__jurisdiction__slug",
                "agency__jurisdiction__level",
                "agency__jurisdiction__parent__abbrev",
                "composer__datetime_submitted",
                "crowdfund_id",
                "date_processing",
            )
            .select_related()
            .prefetch_related(
                make_prefetch(PortalTask),
                make_prefetch(SnailMailTask),
                make_prefetch(PaymentInfoTask),
                Prefetch(
                    "composer__multirequesttask_set",
                    queryset=MultiRequestTask.objects.filter(resolved=False),
                    to_attr="open_multirequesttasks",
                ),
                Prefetch(
                    "agency__newagencytask_set",
                    queryset=NewAgencyTask.objects.filter(resolved=False),
                    to_attr="open_newagencytasks",
                ),
            )
        )
        return objects


class ProcessingRequestList(BaseProcessingRequestList):
    title = "Processing Requests"

    def get_queryset(self):
        return super().get_queryset().filter(status="submitted")


class PortalProcessingRequestList(BaseProcessingRequestList):
    title = "Portal Requests"

    def get_queryset(self):
        return super().get_queryset().filter(communications__portaltask__resolved=False)


class SnailMailProcessingRequestList(BaseProcessingRequestList):
    title = "Snail Mail Requests"

    def get_queryset(self):
        return (
            super().get_queryset().filter(communications__snailmailtask__resolved=False)
        )


@class_view_decorator(login_required)
class ComposerList(MRListView):
    """List to view your composers"""

    model = FOIAComposer
    title = "Your Drafts"
    template_name = "foia/composer_list.html"
    default_sort = "datetime_created"
    default_order = "desc"
    sort_map = {"title": "title", "date_created": "datetime_created"}

    def get_queryset(self):
        """Only show the current user's drafts"""
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user, status="started")
            .prefetch_related("agencies")
        )
