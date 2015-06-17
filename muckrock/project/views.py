"""
Views for the project application
"""

from django.shortcuts import render, redirect
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

    def post(self, request):
        """Creates a project based on the received data"""
        form = self.form_class(request.POST)
        if form.is_valid():
            # create the project
            # return redirect(project)
            pass
        return render(request, self.template_name, {'form': form})
