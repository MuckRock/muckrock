"""
Admin registration for FOIA models
"""

from django.contrib import admin

from foia.models import FOIARequest, FOIAImage, FOIAFile, Jurisdiction, Agency, AgencyType

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
    list_display = ('title', 'user', 'status')
    list_filter = ['status']
    search_fields = ['title', 'request', 'response']
    inlines = [FOIAImageInline, FOIAFileInline]


class JurisdictionAdmin(admin.ModelAdmin):
    """Jurisdiction admin options"""
    # pylint: disable-msg=R0904

    list_display = ('name', 'level')
    list_filter = ['level']
    search_fields = ['name']


class AgencyTypeAdmin(admin.ModelAdmin):
    """AgencyType admin options"""
    # pylint: disable-msg=R0904

    list_display = ('name', )
    search_fields = ['name']


class AgencyAdmin(admin.ModelAdmin):
    """Agency admin options"""
    # pylint: disable-msg=R0904

    list_display = ('name', 'jurisdiction')
    list_filter = ['jurisdiction', 'types']


admin.site.register(FOIARequest,  FOIARequestAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
admin.site.register(AgencyType,   AgencyTypeAdmin)
admin.site.register(Agency,       AgencyAdmin)

