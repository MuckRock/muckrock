"""
Views for the project application
"""

from django.shortcuts import render, redirect
from django.views.generic import View, DetailView
from django.utils.text import slugify

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
            project = form.save(commit=False)
            project.slug = slugify(project.title)
            project.save()
            return redirect(project)
        return render(request, self.template_name, {'form': form})

class ProjectDetailView(DetailView):
    """Detail about a specific project"""
    model = Project
    template_name = 'project/detail.html'
