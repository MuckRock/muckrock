"""
Admin registration for FOIA models
"""

from django.contrib import admin

from foia.models import FOIARequest, FOIAImage

class FOIAImageInline(admin.TabularInline):
    """FOIA Image Inline admin options"""
    model = FOIAImage
    extra = 3

class FOIARequestAdmin(admin.ModelAdmin):
    """FOIA Request admin options"""
    # pylint: disable-msg=R0904

    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status', 'jurisdiction')
    list_filter = ['status', 'jurisdiction']
    search_fields = ['title', 'request', 'response']
    inlines = [ FOIAImageInline, ]

admin.site.register(FOIARequest, FOIARequestAdmin)

