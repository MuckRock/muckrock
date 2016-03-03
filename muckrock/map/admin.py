"""
Admin registration for Map models
"""

from django import forms
from django.contrib import admin

import autocomplete_light
from reversion import VersionAdmin

from muckrock.foia.models import FOIARequest
from muckrock.map.models import Map, Marker

class MarkerAdminForm(forms.ModelForm):

    foia = autocomplete_light.ModelChoiceField(
        'FOIARequestAdminAutocomplete',
        queryset=FOIARequest.objects.all(),
        required=False,
        label='FOIA Request'
    )

    class Meta:
        model = Marker
        fields = '__all__'

class MarkerInline(admin.TabularInline):
    """Marker inline settings"""
    model = Marker
    form = MarkerAdminForm
    extra = 0

class MapAdmin(VersionAdmin):
    """Map admin interface settings"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'project', 'private', 'date_created', 'date_updated')
    list_filter = ['project']
    search_fields = ['title']
    inlines = [MarkerInline]

admin.site.register(Map, MapAdmin)
