"""
Admin registration for Crowdfunding
"""

from django.contrib import admin

from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundReuqestPayment

class CrowdfundRequestAdmin(admin.ModelAdmin):
    """Model Admin for crowdfund request"""

admin.site.register(CrowdfundRequest, CrowdfundRequestAdmin)
