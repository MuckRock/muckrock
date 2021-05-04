"""
Admin registration for Tasks
"""

# Django
from django.contrib import admin

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.task.models import (
    BlacklistDomain,
    CrowdfundTask,
    FileDownloadLink,
    FlaggedTask,
    MultiRequestTask,
    NewAgencyTask,
    OrphanTask,
    PortalTask,
    ProjectReviewTask,
    RejectedEmailTask,
    ResponseTask,
    SnailMailTask,
)


class OrphanTaskAdmin(VersionAdmin):
    """Orphan Task Admin"""

    readonly_fields = ["communication"]


class SnailMailTaskAdmin(VersionAdmin):
    """Snail Mail Task Admin"""

    readonly_fields = ["communication", "amount"]


class RejectedEmailTaskAdmin(VersionAdmin):
    """Rejected Email Task Admin"""

    readonly_fields = ["foia"]


class FlaggedTaskAdmin(VersionAdmin):
    """Flagged Task Admin"""

    readonly_fields = ["user", "foia", "jurisdiction", "agency"]


class ProjectReviewTaskAdmin(VersionAdmin):
    """Flagged Task Admin"""

    readonly_fields = ["notes", "project"]


class NewAgencyTaskAdmin(VersionAdmin):
    """New Agency Task Admin"""

    readonly_fields = ["user", "agency"]


class ResponseTaskAdmin(VersionAdmin):
    """Response Task Admin"""

    readonly_fields = ["communication"]


class CrowdfundTaskAdmin(VersionAdmin):
    """Crowdfund Task Admin"""

    readonly_fields = ["crowdfund"]


class MultiRequestTaskAdmin(VersionAdmin):
    """MultiRequest Task Admin"""

    readonly_fields = ["composer", "assigned", "resolved_by"]


class PortalTaskAdmin(VersionAdmin):
    """Portal Task Admin"""

    readonly_fields = ["communication"]


class FileDownloadLinkAdmin(VersionAdmin):
    """File Download Link Admin"""

    list_display = ["name", "url"]


admin.site.register(OrphanTask, OrphanTaskAdmin)
admin.site.register(SnailMailTask, SnailMailTaskAdmin)
admin.site.register(RejectedEmailTask, RejectedEmailTaskAdmin)
admin.site.register(FlaggedTask, FlaggedTaskAdmin)
admin.site.register(ProjectReviewTask, ProjectReviewTaskAdmin)
admin.site.register(NewAgencyTask, NewAgencyTaskAdmin)
admin.site.register(ResponseTask, ResponseTaskAdmin)
admin.site.register(CrowdfundTask, CrowdfundTaskAdmin)
admin.site.register(MultiRequestTask, MultiRequestTaskAdmin)
admin.site.register(PortalTask, PortalTaskAdmin)
admin.site.register(BlacklistDomain)
admin.site.register(FileDownloadLink, FileDownloadLinkAdmin)
