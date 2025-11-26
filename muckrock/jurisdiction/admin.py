"""
Admin registration for Jurisdiction models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.shortcuts import get_object_or_404
from django.urls import re_path

# Standard Library
import logging

# Third Party
from dal import forward
from reversion.admin import VersionAdmin
from simple_history.admin import SimpleHistoryAdmin

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core import autocomplete
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import (
    ExampleAppeal,
    Exemption,
    GeminiFileSearchStore,
    InvokedExemption,
    Jurisdiction,
    JurisdictionPage,
    JurisdictionResource,
    Law,
)
from muckrock.jurisdiction.views import detail

logger = logging.getLogger(__name__)


class LawInline(admin.StackedInline):
    """Law admin options"""

    model = Law
    extra = 0
    exclude = ["law_analysis"]


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


class JurisdictionAdminForm(forms.ModelForm):
    """Jurisdiction admin form"""

    appeal_agency = forms.ModelChoiceField(
        queryset=Agency.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            forward=(
                forward.Field("id", "jurisdiction"),
                forward.Const(True, "appeal"),
            ),
            attrs={"data-placeholder": "Agency?", "data-width": None},
        ),
    )
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Jurisdiction
        fields = "__all__"


class JurisdictionAdmin(VersionAdmin):
    """Jurisdiction admin options"""

    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "parent", "level")
    list_filter = ["level"]
    search_fields = ["name"]
    inlines = [LawInline]
    filter_horizontal = ("holidays",)
    form = JurisdictionAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
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
                    "appeal_agency",
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


class JurisdictionPageForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.Textarea())

    class Meta:
        model = JurisdictionPage
        fields = "__all__"


class JurisdictionPageAdmin(SimpleHistoryAdmin):
    list_select_related = ["jurisdiction"]
    autocomplete_fields = ["jurisdiction"]
    form = JurisdictionPageForm

    def save_model(self, request, obj, form, change):
        # pylint: disable=protected-access
        obj._change_reason = form.cleaned_data["reason"]
        cache.delete(
            make_template_fragment_key("jurisdiction_detail", [obj.jurisdiction.pk])
        )
        return super().save_model(request, obj, form, change)

    def get_urls(self):
        """Add custom URLs here"""
        urls = super().get_urls()
        my_urls = [
            re_path(
                r"^preview/(?P<idx>\d+)/$",
                self.admin_site.admin_view(self.preview),
                name="jurisdiction-page-preview",
            ),
        ]
        return my_urls + urls

    def preview(self, request, idx):
        """Preview the jurisdiction page"""
        page = get_object_or_404(JurisdictionPage, pk=idx)
        cache.delete(
            make_template_fragment_key("jurisdiction_detail", [page.jurisdiction.pk])
        )
        if page.jurisdiction.level == "f":
            fed_slug = page.jurisdiction.slug
            state_slug = None
            local_slug = None
        elif page.jurisdiction.level == "s":
            fed_slug = page.jurisdiction.parent.slug
            state_slug = page.jurisdiction.slug
            local_slug = None
        else:
            fed_slug = page.jurisdiction.parent.parent.slug
            state_slug = page.jurisdiction.parent.slug
            local_slug = page.jurisdiction.slug
        return detail(
            request, fed_slug, state_slug, local_slug, request.POST.get("content")
        )


class JurisdictionResourceAdminForm(forms.ModelForm):
    """Form to include jurisdiction autocomplete"""

    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(level="s"),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Jurisdiction?", "data-width": None},
        ),
    )

    class Meta:
        model = JurisdictionResource
        fields = "__all__"


class JurisdictionResourceAdmin(admin.ModelAdmin):
    """Admin for JurisdictionResource"""

    list_display = (
        "display_name",
        "jurisdiction",
        "resource_type",
        "index_status",
        "is_active",
        "created_at",
    )
    list_filter = ["jurisdiction", "resource_type", "index_status", "is_active"]
    search_fields = ["display_name", "description", "jurisdiction__name"]
    readonly_fields = [
        "gemini_file_id",
        "gemini_display_name",
        "indexed_at",
        "created_at",
        "updated_at",
    ]
    form = JurisdictionResourceAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "jurisdiction",
                    "display_name",
                    "description",
                    "resource_type",
                    "file",
                    "order",
                    "is_active",
                )
            },
        ),
        (
            "Gemini Integration",
            {
                "classes": ("collapse",),
                "fields": (
                    "index_status",
                    "gemini_file_id",
                    "gemini_display_name",
                    "indexed_at",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


class GeminiFileSearchStoreAdmin(admin.ModelAdmin):
    """Admin for GeminiFileSearchStore"""

    list_display = (
        "display_name",
        "store_name",
        "is_active",
        "total_files",
        "last_sync_at",
    )
    readonly_fields = ["created_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "display_name",
                    "store_name",
                    "is_active",
                )
            },
        ),
        (
            "Stats",
            {
                "fields": ("total_files", "last_sync_at", "created_at"),
            },
        ),
    )


admin.site.register(Exemption, ExemptionAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
admin.site.register(JurisdictionPage, JurisdictionPageAdmin)
admin.site.register(JurisdictionResource, JurisdictionResourceAdmin)
admin.site.register(GeminiFileSearchStore, GeminiFileSearchStoreAdmin)
