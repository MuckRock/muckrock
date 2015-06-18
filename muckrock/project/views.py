"""
Views for the project application
"""

from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm

class ProjectCreateView(CreateView):
    """Create a project instance"""
    form_class = ProjectCreateForm
    template_name = 'project/create.html'

class ProjectDetailView(DetailView):
    """View a project instance"""
    model = Project
    template_name = 'project/detail.html'

class ProjectUpdateView(UpdateView):
    """Update a project instance"""
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'project/update.html'

class ProjectDeleteView(DeleteView):
    """Delete a project instance"""
    model = Project
    success_url = reverse_lazy('index')
    template_name = 'project/delete.html'
