"""
Admin interface for projects
"""

from django import forms
from django.contrib import admin

import autocomplete_light
from reversion import VersionAdmin

from muckrock.foia.models import FOIARequest
from muckrock.project.models import Project


class ProjectAdminForm(forms.ModelForm):
    """Form to include autocomplete fields"""
    requests = autocomplete_light.ModelMultipleChoiceField(
            'FOIARequestAdminAutocomplete',
            queryset=FOIARequest.objects.all(),
            required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Project
        fields = '__all__'


class ProjectAdmin(VersionAdmin):
    """Admin interface for Project model"""
    form = ProjectAdminForm
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'private')
    search_fields = ('title', 'description')
    filter_horizontal = ('contributors', 'articles')


admin.site.register(Project, ProjectAdmin)
