"""
Forms for the project application
"""

from django import forms

from muckrock.project.models import Project

class ProjectCreateForm(forms.ModelForm):
    """Form for creating a new project"""

    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'contributors', 'tags']

class ProjectUpdateForm(forms.ModelForm):
    """Form for updating a project instance"""

    class Meta:
        model = Project
        fields = ['description', 'image', 'contributors', 'tags', 'requests', 'articles']
