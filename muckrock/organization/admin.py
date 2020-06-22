"""
Admin registration for organization models
"""

# Django
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.organization.models import Entitlement, Organization


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    list_display = ('name', 'entitlement', 'private', 'individual')
    list_filter = ('entitlement', 'private', 'individual')
    search_fields = ('name', 'users__username')
    fields = (
        'uuid',
        'name',
        'slug',
        'private',
        'individual',
        'entitlement',
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
        'entitlement',
        'card',
        'requests_per_month',
        'date_update',
    )

    def get_fields(self, request, obj=None):
        """Only add user link for individual organizations"""
        if obj and obj.individual:
            return ('user_link',) + self.fields
        else:
            return self.fields

    def get_readonly_fields(self, request, obj=None):
        """Only add user link for individual organizations"""
        if obj and obj.individual:
            return ('user_link',) + self.readonly_fields
        else:
            return self.readonly_fields

    def user_link(self, obj):
        """Link to the individual org's user"""
        user = User.objects.get(profile__uuid=obj.uuid)
        link = reverse('admin:auth_user_change', args=(user.pk,))
        return '<a href="%s">%s</a>' % (link, user.username)

    user_link.allow_tags = True
    user_link.short_description = 'User'


class EntitlementAdmin(VersionAdmin):
    """Entitlement Admin"""
    list_display = (
        'name',
        'minimum_users',
        'base_requests',
        'requests_per_user',
        'feature_level',
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Entitlement, EntitlementAdmin)
