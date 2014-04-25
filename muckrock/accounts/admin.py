"""
Admin registration for accounts models
"""

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from reversion import VersionAdmin

from muckrock.accounts.models import Profile, Statistics

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class StatisticsAdmin(VersionAdmin):
    """Statistics admin options"""
    list_display = ('date', 'total_requests', 'total_requests_success', 'total_requests_denied',
                    'total_pages', 'total_users', 'total_agencies', 'total_fees')
    formats = ['xls', 'csv']


class ProfileAdmin(VersionAdmin):
    """Profile admin options"""
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

admin.site.register(Statistics, StatisticsAdmin)
admin.site.register(Profile, ProfileAdmin)

UserAdmin.list_display += ('date_joined',)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
