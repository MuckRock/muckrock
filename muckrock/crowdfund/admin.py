"""
Admin registration for Crowdfunding
"""

from django.contrib import admin

from reversion.admin import VersionAdmin

from muckrock.crowdfund import models

# pylint: disable=too-many-public-methods

class CrowdfundPaymentAdmin(admin.TabularInline):
    """Model Admin for crowdfund payment"""
    model = models.CrowdfundPayment
    readonly_fields = ('user', 'name', 'date', 'amount', 'show')
    extra = 0


class CrowdfundAdmin(VersionAdmin):
    """Model Admin for crowdfund"""
    list_display = ('name', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundPaymentAdmin]

admin.site.register(models.Crowdfund, CrowdfundAdmin)
