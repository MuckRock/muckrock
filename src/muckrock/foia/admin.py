"""
Admin registration for FOIA models
"""

from django.contrib import admin

from foia.models import FOIARequest, FOIAImage, FOIAFile

class FOIAImageInline(admin.TabularInline):
    """FOIA Image Inline admin options"""
    model = FOIAImage
    extra = 3


class FOIAFileInline(admin.TabularInline):
    """FOIA File Inline admin options"""
    model = FOIAFile
    extra = 1


class FOIARequestAdmin(admin.ModelAdmin):
    """FOIA Request admin options"""
    # pylint: disable-msg=R0904

    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status', 'jurisdiction')
    list_filter = ['status', 'jurisdiction']
    search_fields = ['title', 'request', 'response']
    inlines = [FOIAImageInline, FOIAFileInline]

admin.site.register(FOIARequest, FOIARequestAdmin)

