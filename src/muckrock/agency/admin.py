"""
Admin registration for Agency models
"""

from django.contrib import admin

from agency.models import AgencyType, Agency

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class AgencyTypeAdmin(admin.ModelAdmin):
    """AgencyType admin options"""
    list_display = ('name', )
    search_fields = ['name']


class AgencyAdmin(admin.ModelAdmin):
    """Agency admin options"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'jurisdiction')
    list_filter = ['approved', 'jurisdiction', 'types']
    search_fields = ['name']

admin.site.register(AgencyType, AgencyTypeAdmin)
admin.site.register(Agency,     AgencyAdmin)
