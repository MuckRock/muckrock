"""
Admin registration for Sidebar
"""

# Django
from django.contrib import admin

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.sidebar.models import Broadcast


class BroadcastAdmin(VersionAdmin):
    """Sidebar admin options"""
    list_display = ('context',)


admin.site.register(Broadcast, BroadcastAdmin)
