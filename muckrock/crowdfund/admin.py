"""
Admin registration for Crowdfunding
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.crowdfund import models

# pylint: disable=too-many-public-methods

class CrowdfundPaymentAdminForm(forms.ModelForm):
    """Form for crowdfund payment inline"""

    user = autocomplete_light.ModelChoiceField(
            'UserAutocomplete',
            label='User',
            queryset=User.objects.all(),
            required=False)

    class Meta:
        model = models.CrowdfundPayment
        fields = '__all__'


class CrowdfundPaymentAdmin(admin.TabularInline):
    """Model Admin for crowdfund payment"""
    form = CrowdfundPaymentAdminForm
    model = models.CrowdfundPayment
    readonly_fields = ('recurring',)
    extra = 0


class CrowdfundAdmin(VersionAdmin):
    """Model Admin for crowdfund"""
    list_display = ('name', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundPaymentAdmin]
    search_fields = ('name',)


class RecurringCrowdfundPaymentAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    user = autocomplete_light.ModelChoiceField(
            'UserAutocomplete',
            queryset=User.objects.all(),
            required=False,
            )

    class Meta:
        # pylint: disable=too-few-public-methods
        model = models.RecurringCrowdfundPayment
        fields = '__all__'


class RecurringCrowdfundPaymentAdmin(VersionAdmin):
    """Recurring donation admin options"""
    model = models.RecurringCrowdfundPayment
    list_display = (
            'email',
            'user',
            'crowdfund',
            'amount',
            'payment_failed',
            'active',
            'created_datetime',
            )
    list_select_related = ('user',)
    search_fields = ('email', 'user__username', 'crowdfund__name')
    form = RecurringCrowdfundPaymentAdminForm
    date_hierarchy = 'created_datetime'
    list_filter = ('active', 'payment_failed')
    readonly_fields = (
            'email',
            'crowdfund',
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
        return super(RecurringCrowdfundPaymentAdmin, self).save_model(
                request, obj, form, change)


admin.site.register(models.Crowdfund, CrowdfundAdmin)
admin.site.register(
        models.RecurringCrowdfundPayment,
        RecurringCrowdfundPaymentAdmin,
        )
