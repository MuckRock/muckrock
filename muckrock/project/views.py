"""
Views for the project application
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import exceptions
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

from actstream import action

from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm

class ProjectListView(ListView):
    """List all projects"""
    model = Project
    template_name = 'project/list.html'
    paginate_by = 25

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
        self.object = form.save()
        action.send(self.request.user, verb='created', target=self.object)
        return HttpResponseRedirect(self.get_success_url())

class ProjectDetailView(DetailView):
    """View a project instance"""
    model = Project
    template_name = 'project/detail.html'

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
            raise exceptions.PermissionDenied()
        return super(ProjectPermissionsMixin, self).dispatch(*args, **kwargs)

class ProjectUpdateView(ProjectPermissionsMixin, UpdateView):
    """Update a project instance"""
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'project/update.html'

class ProjectDeleteView(ProjectPermissionsMixin, DeleteView):
    """Delete a project instance"""
    model = Project
    success_url = reverse_lazy('index')
    template_name = 'project/delete.html'
