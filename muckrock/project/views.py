"""
Views for the project application
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
)

# Standard Library
from datetime import date, timedelta

# Third Party
from actstream.models import followers

# MuckRock
from muckrock.accounts.utils import mixpanel_event
from muckrock.core.utils import new_action
from muckrock.core.views import MRAutocompleteView, MRSearchFilterListView
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.crowdfund.models import Crowdfund
from muckrock.message.tasks import notify_project_contributor
from muckrock.project.filters import ProjectFilterSet
from muckrock.project.forms import (
    ProjectCreateForm,
    ProjectPublishForm,
    ProjectUpdateForm,
)
from muckrock.project.models import Project, ProjectCrowdfunds


class ProjectExploreView(TemplateView):
    """Provides a space for exploring our different projects."""

    template_name = "project/explore.html"

    def get_context_data(self, **kwargs):
        """Gathers and returns a dictionary of context."""
        context = super(ProjectExploreView, self).get_context_data(**kwargs)
        user = self.request.user
        featured_projects = (
            Project.objects.get_visible(user).filter(featured=True).optimize()
        )
        context.update({"featured_projects": featured_projects})
        return context


class ProjectListView(MRSearchFilterListView):
    """List all projects"""

    model = Project
    title = "Projects"
    template_name = "project/list.html"
    filter_class = ProjectFilterSet
    default_sort = "title"

    def get_queryset(self):
        """Only returns projects that are visible to the current user."""
        queryset = super(ProjectListView, self).get_queryset()
        user = self.request.user
        if user.is_anonymous:
            queryset = queryset.get_public()
        else:
            queryset = queryset.get_visible(user)
        return queryset.optimize()


class ProjectContributorView(ProjectListView):
    """Provides a list of projects that have the user as a contributor."""

    template_name = "project/contributor.html"

    def get_contributor(self):
        """Returns the contributor for the view."""
        return get_object_or_404(User, username=self.kwargs.get("username"))

    def get_queryset(self):
        """Returns all the contributor's projects that are visible to the user."""
        queryset = super(ProjectContributorView, self).get_queryset()
        queryset = queryset.get_for_contributor(self.get_contributor()).get_visible(
            self.request.user
        )
        return queryset

    def get_context_data(self, **kwargs):
        """Gathers and returns the project and the contributor as context."""
        context = super(ProjectContributorView, self).get_context_data(**kwargs)
        contributor = self.get_contributor()
        context.update(
            {
                "user_is_contributor": self.request.user == contributor,
                "contributor": contributor,
                "projects": self.get_queryset(**kwargs),
            }
        )
        return context


class ProjectCreateView(CreateView):
    """Create a project instance"""

    model = Project
    form_class = ProjectCreateForm
    initial = {"private": True}
    template_name = "project/create.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """At the moment, only staff are allowed to create a project."""
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Saves the current user as a contributor to the project."""
        redirection = super(ProjectCreateView, self).form_valid(form)
        project = self.object
        project.contributors.add(self.request.user)
        project.save()
        return redirection


class ProjectDetailView(DetailView):
    """View a project instance"""

    model = Project
    template_name = "project/detail.html"

    def __init__(self, *args, **kwargs):
        self._obj = None
        super(ProjectDetailView, self).__init__(*args, **kwargs)

    def get_object(self, queryset=None):
        """Cache getting the object"""
        if self._obj is not None:
            return self._obj
        self._obj = super(ProjectDetailView, self).get_object(queryset=queryset)
        return self._obj

    def get_context_data(self, **kwargs):
        """Adds visible requests and followers to project context"""
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = context["object"]
        user = self.request.user
        context["sidebar_admin_url"] = reverse(
            "admin:project_project_change", args=(project.pk,)
        )
        visible_requests = project.requests.get_viewable(user).select_related(
            "agency__jurisdiction__parent__parent", "composer__user__profile"
        )
        context["visible_requests"] = visible_requests.get_public_file_count(limit=6)
        context["visible_requests_count"] = visible_requests.count()
        articles = project.articles.get_published().prefetch_related(
            Prefetch("authors", queryset=User.objects.select_related("profile"))
        )
        context["articles"] = articles[:3]
        context["articles_count"] = articles.count()
        context["followers"] = followers(project)
        context["contributors"] = project.contributors.select_related("profile")
        context["user_is_experimental"] = (
            user.is_authenticated and user.profile.experimental
        )
        context["newsletter_label"] = (
            "Subscribe to the project newsletter"
            if not project.newsletter_label
            else project.newsletter_label
        )
        context["newsletter_cta"] = (
            "Get updates delivered to your inbox"
            if not project.newsletter_cta
            else project.newsletter_cta
        )
        context["user_can_edit"] = project.editable_by(user)
        return context

    def dispatch(self, *args, **kwargs):
        """If the project is private it is only visible to contributors and staff."""
        project = self.get_object()
        user = self.request.user
        contributor_or_staff = user.is_staff or project.has_contributor(user)
        public = not project.private and project.approved
        if not public and not contributor_or_staff:
            raise Http404()
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)


class ProjectPermissionsMixin:
    """
    This mixin provides a test to see if the current user is either
    a staff member or a project contributor. If they are, they are
    granted access to the page. If they aren't, a PermissionDenied
    exception is thrown.

    Note: It must be included first when subclassing Django generic views
    because it overrides their dispatch method.
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Overrides the dispatch function to include permissions checking."""
        self.object = get_object_or_404(Project, pk=kwargs.get("pk", None))
        if not self.object.editable_by(self.request.user):
            raise Http404()
        return super(ProjectPermissionsMixin, self).dispatch(*args, **kwargs)


class ProjectEditView(ProjectPermissionsMixin, UpdateView):
    """Update a project instance"""

    model = Project
    template_name = "project/edit.html"
    form_class = ProjectUpdateForm

    def form_valid(self, form):
        """Adds success message when form is valid."""
        existing_contributors = self.object.contributors.all()
        new_contributors = form.cleaned_data["contributors"]
        self.notify_new_contributors(existing_contributors, new_contributors)
        messages.success(self.request, "Your edits were saved.")
        # clear the template cache for the project after its been edited
        self.object.clear_cache()
        return super(ProjectEditView, self).form_valid(form)

    def notify_new_contributors(self, existing, new):
        """Notify all newly added contributors."""
        added_contributors = list(set(new) - set(existing))
        for contributor in added_contributors:
            notify_project_contributor.delay(
                contributor.pk, self.object.pk, self.request.user.pk
            )


class ProjectPublishView(ProjectPermissionsMixin, FormView):
    """Publish a project"""

    model = Project
    template_name = "project/publish.html"
    form_class = ProjectPublishForm

    def dispatch(self, *args, **kwargs):
        """Prevents access to the view for projects that public or pending approval."""
        project = get_object_or_404(Project, pk=kwargs.get("pk", None))
        if project.editable_by(self.request.user):
            if not project.private:
                if project.approved:
                    messages.warning(self.request, "This project is already public.")
                else:
                    messages.warning(
                        self.request,
                        "This project is already published and awaiting approval.",
                    )
                return redirect(project)
        return super(ProjectPublishView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectPublishView, self).get_context_data(**kwargs)
        context["project"] = self.object
        return context

    def form_valid(self, form):
        """Call the Project.publish method using the valid form data."""
        notes = form.cleaned_data["notes"]
        self.object.publish(notes)
        return super(ProjectPublishView, self).form_valid(form)

    def get_success_url(self):
        """Return the project url"""
        return self.object.get_absolute_url()


class ProjectCrowdfundView(ProjectPermissionsMixin, CreateView):
    """A creation view for project crowdfunding"""

    model = Crowdfund
    form_class = CrowdfundForm
    template_name = "project/crowdfund.html"

    def dispatch(self, *args, **kwargs):
        """Crowdfunds may only be started on public projects."""
        return_value = super(ProjectCrowdfundView, self).dispatch(*args, **kwargs)
        project = self.get_project()
        if project.editable_by(self.request.user):
            if project.private or not project.approved:
                messages.warning(
                    self.request, "Crowdfunds may only be started on public requests."
                )
                return redirect(project)
        return return_value

    def get_project(self):
        """Returns the project based on the URL keyword arguments"""
        return self.get_object(queryset=Project.objects.all())

    def get_initial(self):
        """Sets defaults in crowdfund project form"""
        project = self.get_project()
        initial_name = "Crowdfund the " + project.title
        initial_date = date.today() + timedelta(30)
        return {"name": initial_name, "date_due": initial_date, "project": project.id}

    def form_valid(self, form):
        """Saves relationship and sends action before returning URL"""
        redirection = super(ProjectCrowdfundView, self).form_valid(form)
        crowdfund = self.object
        project = self.get_project()
        relationship = ProjectCrowdfunds.objects.create(
            project=project, crowdfund=crowdfund
        )
        new_action(
            self.request.user,
            "began crowdfunding",
            action_object=relationship.crowdfund,
            target=relationship.project,
        )
        crowdfund.send_intro_email(self.request.user)
        mixpanel_event(
            self.request,
            "Launch Project Crowdfund",
            self._project_mixpanel_properties(
                project,
                {
                    "Name": crowdfund.name,
                    "Payment Capped": crowdfund.payment_capped,
                    "Payment Required": float(crowdfund.payment_required),
                    "Date Due": crowdfund.date_due.isoformat(),
                },
            ),
        )
        return redirection

    def get_success_url(self):
        """Generates actions before returning URL"""
        project = self.get_project()
        return project.get_absolute_url()

    def get(self, request, *args, **kwargs):
        response = super(ProjectCrowdfundView, self).get(request, *args, **kwargs)
        mixpanel_event(
            request,
            "Start Project Crowdfund",
            self._project_mixpanel_properties(self.get_project()),
        )
        return response

    def _project_mixpanel_properties(self, project, extra_data=None):
        """Get properties for tracking project events in mixpanel"""
        data = {
            "Title": project.title,
            "ID": project.id,
            "Private": project.private,
            "Approved": project.approved,
            "Featured": project.featured,
            "Created At": project.date_created.isoformat()
            if project.date_created
            else None,
        }
        if extra_data is not None:
            data.update(extra_data)
        return data


class ProjectAutocomplete(MRAutocompleteView):
    """Autocomplete for projects"""

    model = Project
    search_fields = ["title", "summary"]
    template = "autocomplete/project.html"

    def get_queryset(self):

        queryset = super().get_queryset()

        manager = self.forwarded.get("manager")
        if manager:
            queryset = queryset.get_manager(self.request.user)
        else:
            queryset = queryset.get_visible(self.request.user)

        return queryset
