"""
Admin registration for accounts models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.accounts.models import (
    Profile,
    ReceiptEmail,
    RecurringDonation,
    Statistics,
)
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class StatisticsAdmin(VersionAdmin):
    """Statistics admin options"""
    list_display = (
        'date', 'total_requests', 'total_requests_success',
        'total_requests_denied', 'total_pages', 'total_users', 'total_agencies',
        'total_fees'
    )
    formats = ['xls', 'csv']


class ProfileAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    location = autocomplete_light.ModelChoiceField(
        'JurisdictionAdminAutocomplete',
        queryset=Jurisdiction.objects.all(),
        required=False,
    )
    agency = autocomplete_light.ModelChoiceField(
        'AgencyAdminAutocomplete',
        queryset=Agency.objects.filter(status='approved'),
        required=False,
    )

    class Meta:
        model = Profile
        fields = '__all__'


class ProfileInline(admin.StackedInline):
    """Profile admin options"""
    model = Profile
    search_fields = ('user__username', 'full_name')
    form = ProfileAdminForm
    extra = 0
    max_num = 1
    fields = (
        'uuid',
        'full_name',
        'email_confirmed',
        'email_pref',
        'source',
        'location',
        'avatar_url',
        'experimental',
        'use_autologin',
        'email_failed',
        'new_question_notifications',
        'org_share',
        'preferred_proxy',
        'agency',
    )
    readonly_fields = (
        'uuid',
        'full_name',
        'email_confirmed',
        'avatar_url',
    )


class MRUserAdmin(UserAdmin):
    """User admin options"""
    list_display = (
        'username',
        'date_joined',
        'email',
        'full_name',
        'is_staff',
        'is_superuser',
    )
    list_filter = UserAdmin.list_filter
    list_select_related = ('profile',)
    inlines = [ProfileInline]
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('email',)
        }),
        (
            'Permissions', {
                'fields': (
                    'is_active', 'is_staff', 'is_superuser', 'groups',
                    'user_permissions'
                )
            }
        ),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    readonly_fields = (
        'username',
        'email',
    )

    def full_name(self, obj):
        """Show full name from profile"""
        return obj.profile.full_name


class RecurringDonationAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    user = autocomplete_light.ModelChoiceField(
        'UserAutocomplete',
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = RecurringDonation
        fields = '__all__'


# XXX what to do with recurring donations


class RecurringDonationAdmin(VersionAdmin):
    """Recurring donation admin options"""
    model = RecurringDonation
    list_display = (
        'email',
        'user',
        'amount',
        'payment_failed',
        'active',
        'created_datetime',
    )
    list_select_related = ('user',)
    search_fields = ('email', 'user__username')
    form = RecurringDonationAdminForm
    date_hierarchy = 'created_datetime'
    list_filter = ('active', 'payment_failed')
    readonly_fields = (
        'email',
        'created_datetime',
        'amount',
        'customer_id',
        'subscription_id',
        'deactivated_datetime',
    )

    def get_readonly_fields(self, request, obj=None):
        """Return read only fields"""
        if obj.active:
            return self.readonly_fields
        else:
            return self.readonly_fields + ('active',)

    def save_model(self, request, obj, form, change):
        """Cancel the subscription if manually deactivated"""
        if not obj.active:
            obj.cancel()
        return super(RecurringDonationAdmin,
                     self).save_model(request, obj, form, change)


admin.site.register(Statistics, StatisticsAdmin)
admin.site.unregister(User)
admin.site.register(User, MRUserAdmin)
admin.site.register(RecurringDonation, RecurringDonationAdmin)
