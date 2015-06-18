"""
Views for the project application
"""

from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView

from muckrock.project.models import Project
from muckrock.project.forms import CreateProjectForm

class CreateProjectView(CreateView):
    """View for creating a new project."""
    form_class = CreateProjectForm
    template_name = 'project/create.html'

class ProjectDetailView(DetailView):
    """Detail about a specific project"""
    model = Project
    template_name = 'project/detail.html'
