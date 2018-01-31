# -*- coding: utf-8 -*-
"""Admin for the portal app"""

# Django
from django.contrib import admin

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.portal.models import Portal


class PortalAdmin(VersionAdmin):
    """Portal Admin"""
    search_fields = ['name', 'url']
    list_display = ['name', 'url', 'type']
    list_filter = ['type', 'status']


admin.site.register(Portal, PortalAdmin)
