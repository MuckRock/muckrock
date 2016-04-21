"""
Admin registration for Tasks
"""

from django.contrib import admin

from reversion.admin import VersionAdmin

from muckrock.task.models import (
        OrphanTask,
        SnailMailTask,
        RejectedEmailTask,
        StaleAgencyTask,
        FlaggedTask,
        ProjectReviewTask,
        NewAgencyTask,
        ResponseTask,
        GenericTask,
        CrowdfundTask,
        BlacklistDomain,
        )

class OrphanTaskAdmin(VersionAdmin):
    """Orphan Task Admin"""
    readonly_fields = ['communication']

class SnailMailTaskAdmin(VersionAdmin):
    """Snail Mail Task Admin"""
    readonly_fields = ['communication', 'amount']

class RejectedEmailTaskAdmin(VersionAdmin):
    """Rejected Email Task Admin"""
    readonly_fields = ['foia']

class StaleAgencyTaskAdmin(VersionAdmin):
    """Stale Agency Task Admin"""
    readonly_fields = ['agency']

class FlaggedTaskAdmin(VersionAdmin):
    """Flagged Task Admin"""
    readonly_fields = ['user', 'foia', 'jurisdiction', 'agency']

class ProjectReviewTaskAdmin(VersionAdmin):
    """Flagged Task Admin"""
    readonly_fields = ['explanation', 'project']

class NewAgencyTaskAdmin(VersionAdmin):
    """New Agency Task Admin"""
    readonly_fields = ['user', 'agency']

class ResponseTaskAdmin(VersionAdmin):
    """Response Task Admin"""
    readonly_fields = ['communication']

class GenericTaskAdmin(VersionAdmin):
    """Generic Task Admin"""

class CrowdfundTaskAdmin(VersionAdmin):
    """Crowdfund Task Admin"""
    readonly_fields = ['crowdfund']

admin.site.register(OrphanTask, OrphanTaskAdmin)
admin.site.register(SnailMailTask, SnailMailTaskAdmin)
admin.site.register(RejectedEmailTask, RejectedEmailTaskAdmin)
admin.site.register(StaleAgencyTask, StaleAgencyTaskAdmin)
admin.site.register(FlaggedTask, FlaggedTaskAdmin)
admin.site.register(ProjectReviewTask, ProjectReviewTaskAdmin)
admin.site.register(NewAgencyTask, NewAgencyTaskAdmin)
admin.site.register(ResponseTask, ResponseTaskAdmin)
admin.site.register(GenericTask, GenericTaskAdmin)
admin.site.register(CrowdfundTask, CrowdfundTaskAdmin)
admin.site.register(BlacklistDomain)
