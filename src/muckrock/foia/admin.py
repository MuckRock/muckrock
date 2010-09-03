"""
Admin registration for FOIA models
"""

from django.contrib import admin

from foia.models import FOIARequest, FOIADocument, FOIAFile, FOIACommunication, \
                        Jurisdiction, Agency, AgencyType, FOIADocTopViewed
from foia.tasks import upload_document_cloud

# These inhereit more than the allowed number of public methods
# pylint: disable-msg=R0904

class FOIADocumentAdmin(admin.ModelAdmin):
    """FOIA Image Inline admin options"""
    readonly_fields = ['doc_id', 'pages']
    list_display = ('title', 'foia', 'doc_id', 'description')

    def save_model(self, request, obj, form, change):
        """Attach user to article on save"""
        # pylint: disable-msg=E1101
        obj.save()
        # wait 3 seconds to give database a chance to sync
        upload_document_cloud.apply_async(args=[obj.pk, change], countdown=3)


class FOIAFileInline(admin.TabularInline):
    """FOIA File Inline admin options"""
    model = FOIAFile
    extra = 1


class FOIACommunicationInline(admin.TabularInline):
    """FOIA File Inline admin options"""
    model = FOIACommunication
    extra = 1


class FOIARequestAdmin(admin.ModelAdmin):
    """FOIA Request admin options"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status')
    list_filter = ['status']
    search_fields = ['title', 'description']
    inlines = [FOIACommunicationInline, FOIAFileInline]


class JurisdictionAdmin(admin.ModelAdmin):
    """Jurisdiction admin options"""
    list_display = ('name', 'level')
    list_filter = ['level']
    search_fields = ['name']


class AgencyTypeAdmin(admin.ModelAdmin):
    """AgencyType admin options"""
    list_display = ('name', )
    search_fields = ['name']


class AgencyAdmin(admin.ModelAdmin):
    """Agency admin options"""
    list_display = ('name', 'jurisdiction')
    list_filter = ['jurisdiction', 'types']


admin.site.register(FOIARequest,  FOIARequestAdmin)
admin.site.register(FOIADocument, FOIADocumentAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
admin.site.register(AgencyType,   AgencyTypeAdmin)
admin.site.register(Agency,       AgencyAdmin)
admin.site.register(FOIADocTopViewed)
