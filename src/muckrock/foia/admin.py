"""
Admin registration for FOIA models
"""

from django.contrib import admin, messages

from foia.models import FOIARequest, FOIADocument, FOIAImage, FOIAFile, \
                        Jurisdiction, Agency, AgencyType
from foia.utils import upload_document_cloud

# These inhereit more than the allowed number of public methods
# pylint: disable-msg=R0904

class FOIADocumentAdmin(admin.ModelAdmin):
    """FOIA Image Inline admin options"""
    model = FOIADocument
    extra = 1

    def save_model(self, request, obj, form, change):
        """Attach user to article on save"""

        obj.save()
        if not change:
            try:
                info = upload_document_cloud(obj.document.path, obj.title, obj.source,
                                             obj.description, obj.access)
                obj.doc_id = info['id']
                obj.save()
            except IOError:
                messages.error(request, 'There was an error during document cloud processing, '
                                        'please delete this instance and recreate it')
        else:
            messages.info(request, 'Updates made here cannot be propagated to DocumentCloud')


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
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status')
    list_filter = ['status']
    search_fields = ['title', 'request', 'response']
    inlines = [FOIAImageInline, FOIAFileInline]


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

