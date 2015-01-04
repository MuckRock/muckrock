"""
Admin registration for accounts models
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

import autocomplete_light
from reversion import VersionAdmin

from muckrock.accounts.models import Profile, Statistics
from muckrock.jurisdiction.models import Jurisdiction

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class StatisticsAdmin(VersionAdmin):
    """Statistics admin options"""
    list_display = ('date', 'total_requests', 'total_requests_success', 'total_requests_denied',
                    'total_pages', 'total_users', 'total_agencies', 'total_fees')
    formats = ['xls', 'csv']


class ProfileAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    location = autocomplete_light.ModelChoiceField('JurisdictionAdminAutocomplete',
                                                   queryset=Jurisdiction.objects.all(),
                                                   required=False)

    class Meta:
        # pylint: disable=R0903
        model = Profile


class ProfileInline(admin.StackedInline):
    """Profile admin options"""
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    exclude = ('follows_foia', 'follows_question', 'notifications')
    model = Profile
    form = ProfileAdminForm
    extra = 0
    max_num = 1

admin.site.register(Statistics, StatisticsAdmin)

UserAdmin.list_display += ('date_joined',)
UserAdmin.inlines = [ProfileInline]
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
