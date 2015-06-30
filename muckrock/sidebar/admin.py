"""
Admin registration for Sidebar
"""

from django.contrib import admin
from reversion import VersionAdmin
from muckrock.sidebar.models import Sidebar

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods

class SidebarAdmin(VersionAdmin):
    """Sidebar admin options"""
    list_display = ('title',)

admin.site.register(Sidebar, SidebarAdmin)
