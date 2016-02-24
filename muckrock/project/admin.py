"""
Admin interface for projects
"""

from django import forms
from django.contrib import admin

import autocomplete_light
from reversion import VersionAdmin

from muckrock.project.models import Project, ProjectMap

class ProjectMapAdminForm(forms.ModelForm):
    requests = autocomplete_light.ModelMultipleChoiceField('FOIARequestAutocomplete')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = ProjectMap
        fields = '__all__'

class ProjectAdmin(VersionAdmin):
    """Admin interface for Project model"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'private')
    search_fields = ('title', 'description')

class ProjectMapAdmin(VersionAdmin):
    list_display = ('title', 'project')
    search_fields = ('title', 'project')
    form = ProjectMapAdminForm

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectMap, ProjectMapAdmin)
