"""
Admin registration for Sidebar
"""

from django.contrib import admin

from muckrock.sidebar.models import Sidebar

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class SidebarAdmin(admin.ModelAdmin):
    """Sidebar admin options"""
    list_display = ('title',)

admin.site.register(Sidebar, SidebarAdmin)
