"""
Admin display for FOIAMachine models
"""

from django import forms
from django.contrib import admin

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.foiamachine import models
from muckrock.nested_inlines.admin import NestedModelAdmin, NestedTabularInline


class FoiaMachineRequestAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""
    jurisdiction = autocomplete_light.ModelChoiceField('JurisdictionAdminAutocomplete')
    agency = autocomplete_light.ModelChoiceField('AgencyAdminAutocomplete')
    user = autocomplete_light.ModelChoiceField('UserAutocomplete')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = models.FoiaMachineRequest
        fields = '__all__'


class FoiaMachineFileInline(NestedTabularInline):
    """FOIA Machine file inline"""
    model = models.FoiaMachineFile
    exclude = ['communication']
    extra = 0


class FoiaMachineComunicationInline(NestedTabularInline):
    """FOIA Machine communication inline"""
    model = models.FoiaMachineCommunication
    extra = 1
    inlines = [FoiaMachineFileInline]


class FoiaMachineRequestAdmin(NestedModelAdmin, VersionAdmin):
    """FOIA Machine request inline"""
    model = models.FoiaMachineRequest
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status', 'agency', 'jurisdiction')
    list_filter = ['status']
    list_select_related = True
    search_fields = ['title', 'user']
    inlines = [FoiaMachineComunicationInline]
    save_on_top = True
    form = FoiaMachineRequestAdminForm

admin.site.register(models.FoiaMachineRequest, FoiaMachineRequestAdmin)
