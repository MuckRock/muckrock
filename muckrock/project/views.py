"""
Views for the project application
"""

from django.views.generic import CreateView, DetailView, UpdateView

from muckrock.project.models import Project
from muckrock.project.forms import CreateProjectForm, ProjectUpdateForm

class ProjectCreateView(CreateView):
    """Create a project instance."""
    form_class = CreateProjectForm
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
