"""
Admin registration for organization models
"""

# Django
from django.contrib import admin

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.organization.models import Organization

# XXX be careful with admin editing and squarelet


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'private')
    search_fields = ('name', 'users__username')


admin.site.register(Organization, OrganizationAdmin)
