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
    extra = 0


class CrowdfundAdmin(VersionAdmin):
    """Model Admin for crowdfund"""
    list_display = ('name', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundPaymentAdmin]

admin.site.register(models.Crowdfund, CrowdfundAdmin)
