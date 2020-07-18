"""
Admin display for FOIAMachine models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core import autocomplete
from muckrock.foiamachine import models
from muckrock.jurisdiction.models import Jurisdiction


class FoiaMachineRequestAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete", attrs={"data-placeholder": "Jurisdiction?"}
        ),
    )
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.filter(status="approved"),
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            forward=("jurisdiction",),
            attrs={"data-placeholder": "Agency?"},
        ),
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )

    class Meta:
        model = models.FoiaMachineRequest
        fields = "__all__"


class FoiaMachineFileInline(admin.TabularInline):
    """FOIA Machine file inline"""

    model = models.FoiaMachineFile
    extra = 0


class FoiaMachineCommunicationInline(admin.StackedInline):
    """FOIA Machine communication inline"""

    model = models.FoiaMachineCommunication
    extra = 1
    show_change_link = True
    readonly_fields = ("file_count",)
    fields = (
        ("sender", "receiver"),
        ("date", "received"),
        "subject",
        "message",
        "file_count",
    )

    def file_count(self, instance):
        """File count for this communication"""
        return instance.files.count()


class FoiaMachineCommunicationAdmin(VersionAdmin):
    """FOIA Machine communication admin"""

    model = models.FoiaMachineCommunication
    inlines = (FoiaMachineFileInline,)


class FoiaMachineRequestAdmin(VersionAdmin):
    """FOIA Machine request inline"""

    model = models.FoiaMachineRequest
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "user", "status", "agency", "jurisdiction")
    list_filter = ["status"]
    list_select_related = True
    search_fields = ["title", "user__username"]
    inlines = [FoiaMachineCommunicationInline]
    save_on_top = True
    form = FoiaMachineRequestAdminForm


admin.site.register(models.FoiaMachineRequest, FoiaMachineRequestAdmin)
admin.site.register(models.FoiaMachineCommunication, FoiaMachineCommunicationAdmin)
