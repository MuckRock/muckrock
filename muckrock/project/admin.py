"""
Admin interface for projects
"""

from django import forms
from django.contrib import admin

import autocomplete_light
from reversion import VersionAdmin

from muckrock.foia.models import FOIARequest
from muckrock.project.models import Project, ProjectMap

class ProjectMapAdminForm(forms.ModelForm):
    """Adds autocomplete to requests field"""
    requests = autocomplete_light.ModelMultipleChoiceField('FOIARequestAutocomplete')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = ProjectMap
        fields = '__all__'


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


class ProjectMapAdmin(VersionAdmin):
    """Admin interface for ProjectMap models"""
    list_display = ('title', 'project')
    search_fields = ('title', 'project')
    form = ProjectMapAdminForm


admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectMap, ProjectMapAdmin)
