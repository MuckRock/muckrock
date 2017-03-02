"""
Admin display for FOIAMachine models
"""

from django import forms
from django.contrib import admin

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.foiamachine import models


class FoiaMachineRequestAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""
    jurisdiction = autocomplete_light.ModelChoiceField(
            'JurisdictionAdminAutocomplete')
    agency = autocomplete_light.ModelChoiceField('AgencyAdminAutocomplete')
    user = autocomplete_light.ModelChoiceField('UserAutocomplete')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = models.FoiaMachineRequest
        fields = '__all__'


class FoiaMachineFileInline(admin.TabularInline):
    """FOIA Machine file inline"""
    model = models.FoiaMachineFile
    extra = 0


class FoiaMachineCommunicationInline(admin.StackedInline):
    """FOIA Machine communication inline"""
    model = models.FoiaMachineCommunication
    extra = 1
    inlines = (FoiaMachineFileInline,)
    show_change_link = True
    readonly_fields = ('file_count',)
    fields = (
            ('sender', 'receiver'),
            ('date', 'received'),
            'message',
            'file_count',
            )

    def file_count(self, instance):
        """File count for this communication"""
        # pylint: disable=no-self-use
        return instance.files.count()



class FoiaMachineCommunicationAdmin(VersionAdmin):
    """FOIA Machine communication admin"""
    model = models.FoiaMachineCommunication
    inlines = (FoiaMachineFileInline,)


class FoiaMachineRequestAdmin(VersionAdmin):
    """FOIA Machine request inline"""
    model = models.FoiaMachineRequest
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status', 'agency', 'jurisdiction')
    list_filter = ['status']
    list_select_related = True
    search_fields = ['title', 'user']
    inlines = [FoiaMachineCommunicationInline]
    save_on_top = True
    form = FoiaMachineRequestAdminForm

admin.site.register(models.FoiaMachineRequest, FoiaMachineRequestAdmin)
admin.site.register(models.FoiaMachineCommunication, FoiaMachineCommunicationAdmin)
