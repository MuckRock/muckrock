"""
Views for the project application
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponseRedirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

from actstream import action
from actstream.models import followers

from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm


class ProjectListView(ListView):
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


class ProjectCreateView(CreateView):
    """Create a project instance"""
    form_class = ProjectCreateForm
    template_name = 'project/create.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """At the moment, only staff are allowed to create a project."""
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        """Sets current user as a default contributor"""
        queryset = User.objects.filter(pk=self.request.user.pk)
        return {'contributors': queryset}

    def form_valid(self, form):
        """Saves an activity stream action when creating the object"""
        project = form.save()
        action.send(self.request.user, verb='created', target=project)
        return HttpResponseRedirect(project.get_absolute_url())


class ProjectDetailView(DetailView):
    """View a project instance"""
    model = Project
    template_name = 'project/detail.html'

    def get_context_data(self, **kwargs):
        """Adds visible requests and followers to project context"""
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = self.get_object()
        user = self.request.user
        context['visible_requests'] = project.requests.get_viewable(user)
        context['followers'] = followers(project)
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

    def _is_editable_by(self, user):
        """A project is editable by MuckRock staff and project contributors."""
        project = self.get_object()
        return project.has_contributor(user) or user.is_staff

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Overrides the dispatch function to include permissions checking."""
        if not self._is_editable_by(self.request.user):
            raise Http404()
        return super(ProjectPermissionsMixin, self).dispatch(*args, **kwargs)


class ProjectUpdateView(ProjectPermissionsMixin, UpdateView):
    """Update a project instance"""
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'project/update.html'

    def get_context_data(self, **kwargs):
        """Add a list of viewable requests to the context data"""
        context = super(ProjectUpdateView, self).get_context_data(**kwargs)
        project = self.get_object()
        user = self.request.user
        viewable_requests = project.requests.get_viewable(user)
        context['viewable_request_ids'] = [request.id for request in viewable_requests]
        return context

    def generate_actions(self, clean_data):
        """
        Generates a specific set of actions based on the update form. Should create an
        action for each request and article that is added or removed from the project.
        """
        user = self.request.user
        project = self.object
        requests = clean_data['requests']
        articles = clean_data['articles']
        existing_requests = project.requests.all()
        existing_articles = project.articles.all()
        # generate actions for added objects
        for request in requests:
            if request not in existing_requests:
                action.send(user, verb='added', action_object=request, target=project)
        for article in articles:
            if article not in existing_articles:
                action.send(user, verb='added', action_object=article, target=project)
        # generate actions for removing objects
        for existing_request in existing_requests:
            if existing_request not in requests:
                action.send(user, verb='removed', action_object=existing_request, target=project)
        for existing_article in existing_articles:
            if existing_article not in articles:
                action.send(user, verb='removed', action_object=existing_article, target=project)
        # generate a generic action
        action.send(user, verb='updated', target=project)

    def form_valid(self, form):
        """Sends an activity stream action when project is updated."""
        self.generate_actions(form.cleaned_data)
        return super(ProjectUpdateView, self).form_valid(form)


class ProjectDeleteView(ProjectPermissionsMixin, DeleteView):
    """Delete a project instance"""
    model = Project
    success_url = reverse_lazy('index')
    template_name = 'project/delete.html'
