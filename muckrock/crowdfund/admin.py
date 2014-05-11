"""
Admin registration for Crowdfunding
"""

from django.contrib import admin

from reversion import VersionAdmin

from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundRequestPayment

# pylint: disable=R0904

class CrowdfundRequestPaymentAdmin(admin.TabularInline):
    """Model Admin for crowdfund request payment"""

    model = CrowdfundRequestPayment
    readonly_fields = ('user', 'name', 'date', 'amount', 'show')
    extra = 0


class CrowdfundRequestAdmin(VersionAdmin):
    """Model Admin for crowdfund request"""

    list_display = ('foia', 'payment_required', 'payment_received', 'date_due')
    date_hierarchy = 'date_due'
    inlines = [CrowdfundRequestPaymentAdmin]



admin.site.register(CrowdfundRequest, CrowdfundRequestAdmin)
