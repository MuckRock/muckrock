"""
Admin registration for organization models
"""

from django.contrib import admin

from reversion import VersionAdmin

from muckrock.organization.models import Organization

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class OrganizationAdmin(VersionAdmin):
    """Quesiton Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner')

admin.site.register(Organization, OrganizationAdmin)

