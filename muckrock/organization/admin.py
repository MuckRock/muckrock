"""
Admin registration for organization models
"""

# Django
from django.contrib import admin

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.organization.models import Organization, Plan


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'private')
    search_fields = ('name', 'users__username')
    readonly_fields = (
        'uuid',
        'name',
        'slug',
        'private',
        'individual',
        'plan',
        'requests_per_month',
        'monthly_requests',
        'number_requests',
        'date_update',
    )


class PlanAdmin(VersionAdmin):
    """Plan Admin"""
    list_display = (
        'name',
        'minimum_users',
        'base_requests',
        'requests_per_user',
        'feature_level',
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Plan, PlanAdmin)
