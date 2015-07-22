"""
Admin registration for Crowdfunding
"""

from django.contrib import admin

from reversion import VersionAdmin

from muckrock.crowdfund import models

# pylint: disable=too-many-public-methods

class CrowdfundRequestPaymentAdmin(admin.TabularInline):
    """Model Admin for crowdfund request payment"""
    model = models.CrowdfundRequestPayment
    readonly_fields = ('user', 'name', 'date', 'amount', 'show')
    extra = 0

class CrowdfundRequestAdmin(VersionAdmin):
    """Model Admin for crowdfund request"""
    list_display = ('foia', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundRequestPaymentAdmin]

class CrowdfundProjectPaymentAdmin(admin.TabularInline):
    """Model Admin for crowdfund project payment"""
    model = models.CrowdfundProjectPayment
    readonly_fields = ('user', 'name', 'date', 'amount', 'show')
    extra = 0

class CrowdfundProjectAdmin(VersionAdmin):
    """Model Admin for crowdfund project"""
    list_display = ('project', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundProjectPaymentAdmin]

admin.site.register(models.CrowdfundRequest, CrowdfundRequestAdmin)
admin.site.register(models.CrowdfundProject, CrowdfundProjectAdmin)
