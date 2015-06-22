"""
Views for the project application
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import exceptions
from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.utils.decorators import method_decorator

from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm

class ProjectCreateView(CreateView):
    """Create a project instance"""
    form_class = ProjectCreateForm
    template_name = 'project/create.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        """Sets current user as a default contributor"""
        queryset = User.objects.filter(pk=self.request.user.pk)
        return {'contributors': queryset}

class ProjectDetailView(DetailView):
    """View a project instance"""
    model = Project
    template_name = 'project/detail.html'

class ProjectUpdateView(UpdateView):
    """Update a project instance"""
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'project/update.html'

    def _is_editable_by(self, user):
        project = self.get_object()
        return project.has_contributor(user) or user.is_staff

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self._is_editable_by(self.request.user):
            raise exceptions.PermissionDenied()
        return super(ProjectUpdateView, self).dispatch(*args, **kwargs)

class ProjectDeleteView(DeleteView):
    """Delete a project instance"""
    model = Project
    success_url = reverse_lazy('index')
    template_name = 'project/delete.html'
