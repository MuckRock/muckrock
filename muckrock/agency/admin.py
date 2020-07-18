"""
Admin registration for Agency models
"""

# Django
from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify

# Standard Library
import logging
import sys

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from dal import forward
from pdfrw import PdfReader
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.agency.forms import CSVImportForm
from muckrock.agency.models import (
    Agency,
    AgencyAddress,
    AgencyEmail,
    AgencyPhone,
    AgencyRequestForm,
    AgencyRequestFormMapper,
    AgencyType,
)
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.core import autocomplete
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.portal.models import Portal

logger = logging.getLogger(__name__)

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods


class AgencyTypeAdmin(VersionAdmin):
    """AgencyType admin options"""

    list_display = ("name",)
    search_fields = ["name"]


class AgencyAddressAdminForm(forms.ModelForm):
    """AgencyAddress Inline admin form"""

    address = autocomplete_light.ModelChoiceField(
        "AddressAdminAutocomplete", queryset=Address.objects.all()
    )

    class Meta:
        model = AgencyAddress
        fields = "__all__"


class AgencyAddressInline(admin.TabularInline):
    """Inline for agency's addresses"""

    model = AgencyAddress
    form = AgencyAddressAdminForm
    show_change_link = True
    extra = 1


class AgencyEmailAdminForm(forms.ModelForm):
    """AgencyEmail Inline admin form"""

    email = autocomplete_light.ModelChoiceField(
        "EmailAddressAdminAutocomplete", queryset=EmailAddress.objects.all()
    )

    class Meta:
        model = AgencyEmail
        fields = "__all__"


class AgencyEmailInline(admin.TabularInline):
    """Inline for agency's email addresses"""

    model = AgencyEmail
    form = AgencyEmailAdminForm
    extra = 1


class AgencyPhoneAdminForm(forms.ModelForm):
    """AgencyPhone Inline admin form"""

    phone = autocomplete_light.ModelChoiceField(
        "PhoneNumberAdminAutocomplete", queryset=PhoneNumber.objects.all()
    )

    class Meta:
        model = AgencyPhone
        fields = "__all__"


class AgencyPhoneInline(admin.TabularInline):
    """Inline for agency's phone numbers"""

    model = AgencyPhone
    form = AgencyPhoneAdminForm
    extra = 1


class AgencyAdminForm(forms.ModelForm):
    """Agency admin form to order users"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )
    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete", attrs={"data-placeholder": "Jurisdiction?"}
        ),
    )
    appeal_agency = forms.ModelChoiceField(
        queryset=Agency.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            forward=("jurisdiction", forward.Const(True, "appeal")),
            attrs={"data-placeholder": "Agency?"},
        ),
    )
    parent = forms.ModelChoiceField(
        queryset=Agency.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            forward=("jurisdiction",),
            attrs={"data-placeholder": "Agency?"},
        ),
    )

    class Meta:
        model = Agency
        fields = "__all__"


class AgencyAdmin(VersionAdmin):
    """Agency admin options"""

    prepopulated_fields = {"slug": ("name",)}
    list_display = (
        "name",
        "jurisdiction",
        "status",
        "get_types",
        "exempt",
        "uncooperative",
    )
    list_filter = ["status", "exempt", "uncooperative", "types"]
    search_fields = ["name", "aliases"]
    filter_horizontal = ("types",)
    form = AgencyAdminForm
    formats = ["xls", "csv"]
    inlines = (AgencyAddressInline, AgencyEmailInline, AgencyPhoneInline)
    save_on_top = True
    # autocomplete_fields = ["portal"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "aliases",
                    "jurisdiction",
                    "types",
                    "status",
                    "user",
                    "requires_proxy",
                )
            },
        ),
        ("Image", {"fields": ("image", "image_attr_line")}),
        ("Notes", {"fields": ("public_notes", "notes")}),
        ("Related Agencies", {"fields": ("appeal_agency", "parent")}),
        ("Exempt", {"fields": ("exempt", "uncooperative", "exempt_note")}),
        (
            "Contact Information",
            {
                "fields": (
                    "contact_salutation",
                    "contact_first_name",
                    "contact_last_name",
                    "contact_title",
                    "portal",
                    "form",
                    "url",
                    "website",
                    "foia_logs",
                    "foia_guide",
                    "twitter",
                    "twitter_handles",
                )
            },
        ),
    )

    def get_types(self, obj):
        """Return the types for display"""
        return ", ".join(obj.types.values_list("name", flat=True))

    get_types.short_description = "Types"


class AgencyRequestFormMapperInline(admin.TabularInline):
    """Inline for Agency Request Form mapper"""

    model = AgencyRequestFormMapper
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        """Set choices based on the pdf file"""
        formset = super(AgencyRequestFormMapperInline, self).get_formset(
            request, obj, **kwargs
        )
        if obj is None:
            return formset
        obj.form.seek(0)
        template = PdfReader(obj.form)
        try:
            choices = [
                (field.T.decode(), field.T.decode())
                for page in template.Root.Pages.Kids
                for field in page.Annots
                if field.T is not None
            ]
        except TypeError:
            # if template.Root.Pages.Kids or page.Annots is None
            choices = []
        choices = [("", "---")] + choices
        formset.form.base_fields["field"].widget = forms.Select(choices=choices)
        return formset


class AgencyRequestFormAdmin(VersionAdmin):
    """Agency request form admin"""

    inlines = [AgencyRequestFormMapperInline]


admin.site.register(AgencyType, AgencyTypeAdmin)
admin.site.register(Agency, AgencyAdmin)
admin.site.register(AgencyRequestForm, AgencyRequestFormAdmin)


def get_jurisdiction(full_name):
    """Get the jurisdiction from its name and parent"""
    if ", " in full_name:
        name, parent_abbrev = full_name.split(", ")
        parent = Jurisdiction.objects.get(abbrev=parent_abbrev)
        return Jurisdiction.objects.get(name=name, parent=parent).pk
    else:
        return Jurisdiction.objects.exclude(level="l").get(name=full_name).pk


class EmailValidator(object):
    """Class to validate emails"""

    def validate(self, value):
        """Must be blank or an email"""
        if value == "":
            return True
        # validate email will throw a validation error on failure
        validate_email(value)
        return True
