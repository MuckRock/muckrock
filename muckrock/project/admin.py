"""
Admin interface for projects
"""

from django.contrib import admin

from reversion import VersionAdmin

from muckrock.project.models import Project

class ProjectAdmin(VersionAdmin):
    """Admin interface for Project model"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'private')
    search_fields = ('title', 'description')

admin.site.register(Project, ProjectAdmin)
