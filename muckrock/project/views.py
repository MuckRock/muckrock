"""
Views for the project application
"""

from django.shortcuts import render
from django.views.generic import View

from muckrock.project.models import Project
from muckrock.project.forms import CreateProjectForm

class CreateProjectView(View):
    """View for creating a new project."""
    form_class = CreateProjectForm
    template_name = 'project/create.html'

    def get(self, request):
        """Renders a template with a form for creating the project"""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
