"""
Admin registration for Sidebar
"""

from django.contrib import admin
from reversion.admin import VersionAdmin
from muckrock.sidebar.models import Broadcast

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods

class BroadcastAdmin(VersionAdmin):
    """Sidebar admin options"""
    list_display = ('context',)

admin.site.register(Broadcast, BroadcastAdmin)
