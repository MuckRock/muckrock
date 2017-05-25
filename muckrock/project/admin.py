"""
Admin interface for projects
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project


class ProjectAdminForm(forms.ModelForm):
    """Form to include autocomplete fields"""
    requests = autocomplete_light.ModelMultipleChoiceField(
            'FOIARequestAdminAutocomplete',
            queryset=FOIARequest.objects.all(),
            required=False)
    contributors = autocomplete_light.ModelMultipleChoiceField(
            'UserAutocomplete',
            queryset=User.objects.all(),
            required=False)
    articles = autocomplete_light.ModelMultipleChoiceField(
            'ArticleAutocomplete',
            queryset=Article.objects.all(),
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


admin.site.register(Project, ProjectAdmin)
