"""
Admin registration for Tasks
"""

from django.contrib import admin

from muckrock.task.models import OrphanTask, SnailMailTask, RejectedEmailTask, StaleAgencyTask, \
                                 FlaggedTask, NewAgencyTask, ResponseTask

admin.site.register(OrphanTask)
admin.site.register(SnailMailTask)
admin.site.register(RejectedEmailTask)
admin.site.register(StaleAgencyTask)
admin.site.register(FlaggedTask)
admin.site.register(NewAgencyTask)
admin.site.register(ResponseTask)
