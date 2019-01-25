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
    list_display = ('name', 'plan', 'private', 'individual')
    list_filter = ('plan', 'private', 'individual')
    search_fields = ('name', 'users__username')
    fields = (
        'uuid',
        'name',
        'slug',
        'private',
        'individual',
        'plan',
        'card',
        'requests_per_month',
        'monthly_requests',
        'number_requests',
        'date_update',
    )
    readonly_fields = (
        'uuid',
        'name',
        'slug',
        'private',
        'individual',
        'plan',
        'card',
        'requests_per_month',
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
