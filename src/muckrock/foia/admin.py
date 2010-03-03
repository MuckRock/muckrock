"""
Admin registration for FOIA models
"""

from django.contrib import admin
from foia.models import FOIARequest

class FOIARequestAdmin(admin.ModelAdmin):
    """FOIA Request admin options"""
    # pylint: disable-msg=R0904

    list_display = ('title', 'user', 'status', 'jurisdiction')
    list_filter = ['status', 'jurisdiction']
    search_fields = ['title', 'request', 'response']

admin.site.register(FOIARequest, FOIARequestAdmin)

