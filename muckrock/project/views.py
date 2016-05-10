"""
Views for the project application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Count, Prefetch
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView,
    FormView,
    CreateView,
    DetailView,
    UpdateView,
)
from django.utils.decorators import method_decorator

import actstream
from datetime import date, timedelta

from muckrock.crowdfund.models import Crowdfund
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.project.models import Project, ProjectCrowdfunds
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm, ProjectPublishForm
from muckrock.views import MRFilterableListView


class ProjectExploreView(TemplateView):
    """Provides a space for exploring our different projects."""
    template_name = 'project/frontpage.html'

    def get_context_data(self, **kwargs):
        """Gathers and returns a dictionary of context."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        user = self.request.user
        visible_projects = (Project.objects.get_visible(user)
                .order_by('-featured', 'title')
                .annotate(request_count=Count('requests', distinct=True))
                .annotate(article_count=Count('articles', distinct=True))
                .prefetch_related(
                    Prefetch('crowdfunds',
                        queryset=Crowdfund.objects
                            .order_by('-date_due')
                            .annotate(contributors_count=Count('payments'))))
                )
        context = {
            'visible': visible_projects,
        }
        return context


class ProjectListView(MRFilterableListView):
    """List all projects"""
    model = Project
    template_name = 'project/list.html'
    paginate_by = 25

    def get_queryset(self):
        """Only returns projects that are visible to the current user."""
        user = self.request.user
        if user.is_anonymous():
            return Project.objects.get_public()
        else:
            return Project.objects.get_visible(user)


class ProjectContributorView(TemplateView):
    """Provides a list of projects that have the user as a contributor."""
    template_name = 'project/contributor.html'

    def get_context_data(self, **kwargs):
        """Gathers and returns the project and the contributor as context."""
        user = self.request.user
        contributor = get_object_or_404(User, username=kwargs.get('username'))
        # return all the contributor's projects that are visible to the user
        projects = Project.objects.get_for_contributor(contributor).get_visible(user)
        projects = projects.order_by('-featured', 'private', '-approved', 'title')
        context = {
            'user_is_contributor': user == contributor,
            'contributor': contributor,
            'projects': projects
        }
        return context


class ProjectCreateView(CreateView):
    """Create a project instance"""
    model = Project
    form_class = ProjectCreateForm
    initial = {'private': True}
    template_name = 'project/create.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff or u.profile.experimental))
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
    template_name = 'project/detail.html'

    def __init__(self, *args, **kwargs):
        self._obj = None
        super(ProjectDetailView, self).__init__(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        """Cache getting the object"""
        if self._obj is not None:
            return self._obj
        self._obj = super(ProjectDetailView, self).get_object(*args, **kwargs)
        return self._obj

    def get_context_data(self, **kwargs):
        """Adds visible requests and followers to project context"""
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = context['object']
        user = self.request.user
        context['sidebar_admin_url'] = reverse('admin:project_project_change',
            args=(project.pk,))
        context['visible_requests'] = (project.requests
                .get_viewable(user)
                .select_related(
                    'jurisdiction',
                    'jurisdiction__parent',
                    'jurisdiction__parent__parent',
                    'agency__jurisdiction',
                    'user__profile',
                    ))
        context['followers'] = actstream.models.followers(project)
        context['articles'] = project.articles.get_published()
        context['contributors'] = project.contributors.select_related('profile')
        context['user_is_experimental'] = user.is_authenticated() and user.profile.experimental
        context['newsletter_label'] = ('Subscribe to the project newsletter'
                                      if not project.newsletter_label else project.newsletter_label)
        context['newsletter_cta'] = ('Get updates delivered to your inbox'
                                    if not project.newsletter_cta else project.newsletter_cta)
        context['user_can_edit'] = project.editable_by(user)
        return context

    def dispatch(self, *args, **kwargs):
        """If the project is private it is only visible to contributors and staff."""
        project = self.get_object()
        user = self.request.user
        contributor_or_staff = user.is_staff or project.has_contributor(user)
        if project.private and not contributor_or_staff:
            raise Http404()
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)


class ProjectPermissionsMixin(object):
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
        self.object = get_object_or_404(Project, pk=kwargs.get('pk', None))
        if not self.object.editable_by(self.request.user):
            raise Http404()
        return super(ProjectPermissionsMixin, self).dispatch(*args, **kwargs)


class ProjectEditView(ProjectPermissionsMixin, UpdateView):
    """Update a project instance"""
    model = Project
    template_name = 'project/edit.html'
    form_class = ProjectUpdateForm

    def form_valid(self, form):
        """Adds success message when form is valid."""
        messages.success(self.request, 'Your edits were saved.')
        return super(ProjectEditView, self).form_valid(form)


class ProjectPublishView(ProjectPermissionsMixin, FormView):
    """Publish a project"""
    model = Project
    template_name = 'project/publish.html'
    form_class = ProjectPublishForm

    def dispatch(self, *args, **kwargs):
        """Prevents access to the view for projects that public or pending approval."""
        project = get_object_or_404(Project, pk=kwargs.get('pk', None))
        if project.editable_by(self.request.user):
            if not project.private:
                if project.approved:
                    messages.warning(self.request,
                        'This project is already public.')
                else:
                    messages.warning(self.request,
                        'This project is already published and awaiting approval.')
                return redirect(project)
        return super(ProjectPublishView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectPublishView, self).get_context_data(**kwargs)
        context['project'] = self.object
        return context

    def form_valid(self, form):
        """Call the Project.publish method using the valid form data."""
        notes = form.cleaned_data['notes']
        self.object.publish(notes)
        return super(ProjectPublishView, self).form_valid(form)

    def get_success_url(self):
        """Return the project url"""
        return self.object.get_absolute_url()


class ProjectCrowdfundView(ProjectPermissionsMixin, CreateView):
    """A creation view for project crowdfunding"""
    model = Crowdfund
    form_class = CrowdfundForm
    template_name = 'project/crowdfund.html'

    def dispatch(self, *args, **kwargs):
        """Crowdfunds may only be started on public projects."""
        return_value = super(ProjectCrowdfundView, self).dispatch(*args, **kwargs)
        project = self.get_project()
        if project.editable_by(self.request.user):
            if project.private or not project.approved:
                messages.warning(self.request, 'Crowdfunds may only be started on public requests.')
                return redirect(project)
        return return_value

    def get_project(self):
        """Returns the project based on the URL keyword arguments"""
        return self.get_object(queryset=Project.objects.all())

    def get_initial(self):
        """Sets defaults in crowdfund project form"""
        project = self.get_project()
        initial_name = 'Crowdfund the ' + project.title
        initial_date = date.today() + timedelta(30)
        return {
            'name': initial_name,
            'date_due': initial_date,
            'project': project.id
        }

    def form_valid(self, form):
        """Saves relationship and sends action before returning URL"""
        redirection = super(ProjectCrowdfundView, self).form_valid(form)
        crowdfund = self.object
        project = self.get_project()
        relationship = ProjectCrowdfunds.objects.create(project=project, crowdfund=crowdfund)
        actstream.action.send(
            self.request.user,
            verb='started',
            action_object=relationship.crowdfund,
            target=relationship.project
        )
        return redirection

    def get_success_url(self):
        """Generates actions before returning URL"""
        project = self.get_project()
        return project.get_absolute_url()
