"""
Admin interface for projects
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project


class ProjectAdminForm(forms.ModelForm):
    """Form to include autocomplete fields"""

    requests = forms.ModelMultipleChoiceField(
        queryset=FOIARequest.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="foia-request-autocomplete",
            attrs={"data-placeholder": "FOIA?", "data-width": None},
        ),
    )
    contributors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    articles = forms.ModelMultipleChoiceField(
        queryset=Article.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="article-autocomplete",
            attrs={"data-placeholder": "Article?", "data-width": None},
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
