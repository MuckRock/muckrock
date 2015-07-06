"""
Forms for the project application
"""

from django import forms

import autocomplete_light
from muckrock.project.models import Project

class ProjectCreateForm(forms.ModelForm):
    """Form for creating a new project"""

    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'contributors', 'tags', 'private']
        widgets = {'contributors': autocomplete_light.MultipleChoiceWidget('StaffAutocomplete')}
        help_texts = {
            'contributors': ('As the project creator, you are'
                            ' automatically listed as a contributor.'),
        }

class ProjectUpdateForm(forms.ModelForm):
    """Form for updating a project instance"""

    class Meta:
        model = Project
        fields = ['description', 'image', 'contributors', 'tags', 'requests', 'articles']
        widgets = {
            'contributors': autocomplete_light.MultipleChoiceWidget('StaffAutocomplete'),
            'requests': autocomplete_light.MultipleChoiceWidget('FOIARequestAdminAutocomplete'),
            'articles': autocomplete_light.MultipleChoiceWidget('ArticleAutocomplete'),
        }
