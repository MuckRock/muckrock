"""
Admin registration for Jurisdiction models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Standard Library
import logging

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import (
    ExampleAppeal,
    Exemption,
    InvokedExemption,
    Jurisdiction,
    Law,
)

logger = logging.getLogger(__name__)

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods


class LawInline(admin.StackedInline):
    """Law admin options"""

    model = Law
    extra = 0


class ExampleAppealInline(admin.TabularInline):
    """Example appeal inline"""

    model = ExampleAppeal
    extra = 0


class InvokedExemptionAdminForm(forms.ModelForm):
    """Adds an autocomplete to the invoked exemption request field."""

    request = forms.ModelChoiceField(
        queryset=FOIARequest.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="foia-request-autocomplete",
            attrs={"data-placeholder": "FOIA?", "data-width": None},
        ),
    )

    class Meta:
        model = InvokedExemption
        fields = "__all__"


class InvokedExemptionInline(admin.StackedInline):
    """Invoked exemption options"""

    form = InvokedExemptionAdminForm
    model = InvokedExemption
    extra = 0


class JurisdictionAdmin(VersionAdmin):
    """Jurisdiction admin options"""

    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "parent", "level")
    list_filter = ["level"]
    search_fields = ["name"]
    inlines = [LawInline]
    filter_horizontal = ("holidays",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "abbrev",
                    "level",
                    "parent",
                    "hidden",
                    "image",
                    "image_attr_line",
                    "public_notes",
                    "aliases",
                )
            },
        ),
        (
            "Options for states/federal",
            {
                "classes": ("collapse",),
                "fields": ("always_proxy", "observe_sat", "holidays"),
            },
        ),
    )
    formats = ["xls", "csv"]


class ExemptionAdminForm(forms.ModelForm):
    """Form to include a jurisdiction and contributor autocomplete"""

    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Jurisdiction?", "data-width": None},
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

    class Meta:
        model = Exemption
        fields = "__all__"


class ExemptionAdmin(VersionAdmin):
    """Provides a way to create and modify exemption information."""

    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "jurisdiction")
    list_filter = ["jurisdiction__level"]
    search_fields = ["name", "basis", "jurisdiction__name"]
    inlines = [ExampleAppealInline, InvokedExemptionInline]
    form = ExemptionAdminForm


admin.site.register(Exemption, ExemptionAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
