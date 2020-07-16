"""
Admin interface for projects
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project


class ProjectAdminForm(forms.ModelForm):
    """Form to include autocomplete fields"""

    requests = autocomplete_light.ModelMultipleChoiceField(
        "FOIARequestAdminAutocomplete",
        queryset=FOIARequest.objects.all(),
        required=False,
    )
    contributors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )
    articles = forms.ModelMultipleChoiceField(
        queryset=Article.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="article-autocomplete", attrs={"data-placeholder": "Article?"}
        ),
    )

    class Meta:
        model = Project
        fields = "__all__"


class ProjectAdmin(VersionAdmin):
    """Admin interface for Project model"""

    form = ProjectAdminForm
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "private", "approved", "featured")
    list_filter = ("approved", "private", "featured")
    search_fields = ("title", "description", "summary")


admin.site.register(Project, ProjectAdmin)
