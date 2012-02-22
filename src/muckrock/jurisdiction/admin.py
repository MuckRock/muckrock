"""
Admin registration for Jurisdiction models
"""

from django.contrib import admin

#from jurisdiction.models import Jurisdiction
from foia.models import Jurisdiction

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class JurisdictionAdmin(admin.ModelAdmin):
    """Jurisdiction admin options"""
    list_display = ('name', 'level')
    list_filter = ['level']
    search_fields = ['name']

admin.site.register(Jurisdiction, JurisdictionAdmin)
