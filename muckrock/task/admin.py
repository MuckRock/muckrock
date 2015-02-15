"""
Admin registration for Tasks
"""

from reversion import VersionAdmin

from django.contrib import admin

from muckrock.task.models import OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask

class OrphanTaskAdmin(VersionAdmin):
    """Orphan Task Admin"""
    readonly_fields = ['communication']

class SnailMailTaskAdmin(VersionAdmin):
    """Snail Mail Task Admin"""
    readonly_fields = ['communication']

class RejectedEmailTaskAdmin(VersionAdmin):
    """Rejected Email Task Admin"""
    readonly_fields = ['foia']

class StaleAgencyTaskAdmin(VersionAdmin):
    """Stale Agency Task Admin"""
    readonly_fields = ['agency']

class FlaggedTaskAdmin(VersionAdmin):
    """Flagged Task Admin"""
    readonly_fields = ['user', 'foia', 'jurisdiction', 'agency']

class NewAgencyTaskAdmin(VersionAdmin):
    """New Agency Task Admin"""
    readonly_fields = ['user', 'agency']

class RepsponseTaskAdmin(VersionAdmin):
    """Response Task Admin"""
    readonly_fields = ['communication']

admin.site.register(OrphanTask, OrphanTaskAdmin)
admin.site.register(SnailMailTask, SnailMailTaskAdmin)
admin.site.register(RejectedEmailTask, RejectedEmailTaskAdmin)
admin.site.register(StaleAgencyTask, StaleAgencyTaskAdmin)
admin.site.register(FlaggedTask, FlaggedTaskAdmin)
admin.site.register(NewAgencyTask, NewAgencyTaskAdmin)
admin.site.register(ResponseTask, ResponseTaskAdmin)
