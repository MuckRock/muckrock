"""
Forms for the project application
"""

from django import forms

from muckrock.project.models import Project

class CreateProjectForm(forms.ModelForm):
    """Form for creating a new project"""

    class Meta:
        model = Project
        fields = ['title']

class ProjectUpdateForm(forms.ModelForm):
    """Form for updating a project instance"""

    class Meta:
        model = Project
        fields = ['description']
