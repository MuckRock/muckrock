"""
Admin registration for FOIA models
"""

from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import simple

from datetime import date, timedelta

from foia.models import FOIARequest, FOIADocument, FOIAFile, FOIACommunication, FOIANote, \
                        Jurisdiction, Agency, AgencyType, FOIADocTopViewed
from foia.tasks import upload_document_cloud, set_document_cloud_pages

# These inhereit more than the allowed number of public methods
# pylint: disable-msg=R0904

class FOIADocumentAdmin(admin.ModelAdmin):
    """FOIA Document admin options"""
    readonly_fields = ['doc_id', 'pages']
    list_display = ('title', 'foia', 'doc_id', 'description')

    def save_model(self, request, obj, form, change):
        """Upload document to Document Cloud on save"""
        # pylint: disable-msg=E1101
        obj.save()
        # wait 3 seconds to give database a chance to sync
        upload_document_cloud.apply_async(args=[obj.pk, change], countdown=3)

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(FOIADocumentAdmin, self).get_urls()
        my_urls = patterns('', url(r'^retry_pages/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.retry_pages),
                                   name='doc-admin-retry-pages'))
        return my_urls + urls

    def retry_pages(self, request, idx):
        """Retry getting the page count"""
        # pylint: disable-msg=E1101
        # pylint: disable-msg=R0201

        doc = get_object_or_404(FOIADocument, pk=idx)
        if doc.pages:
            messages.info(request, 'This document already has its page count set')
        else:
            set_document_cloud_pages.apply_async(args=[doc.pk])
            messages.info(request, 'Attempting to set the page count... Please wait while the '
                                   'Document Cloud servers are being accessed')
        return HttpResponseRedirect(reverse('admin:foia_foiadocument_change', args=[doc.pk]))


class FOIAFileInline(admin.TabularInline):
    """FOIA File Inline admin options"""
    model = FOIAFile
    extra = 1


class FOIACommunicationInline(admin.TabularInline):
    """FOIA Communication Inline admin options"""
    model = FOIACommunication
    extra = 1


class FOIANoteInline(admin.TabularInline):
    """FOIA Notes Inline admin options"""
    model = FOIANote
    extra = 1


class FOIARequestAdmin(admin.ModelAdmin):
    """FOIA Request admin options"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status')
    list_filter = ['status']
    search_fields = ['title', 'description', 'tracking_id', 'mail_id']
    readonly_fields = ['mail_id']
    inlines = [FOIACommunicationInline, FOIAFileInline, FOIANoteInline]

    def save_model(self, request, obj, form, change):
        """Actions to take when a request is saved from the admin"""

        #If changing to completed and embargoed, set embargo date to 30 days out
        if obj.status in ['done', 'partial'] and obj.embargo and not obj.date_embargo:
            obj.date_embargo = date.today() + timedelta(30)

        # if we change the status or add a communication, send the user an update notification
        old_request = obj.get_saved()
        if old_request and (obj.status != old_request.status or
                            obj.communications.count() != old_request.communications.count()):
            obj.updated()

        obj.save()

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(FOIARequestAdmin, self).get_urls()
        my_urls = patterns('', url(r'^process/$', self.admin_site.admin_view(self.process),
                                   name='foia-admin-process'),
                               url(r'^followup/$', self.admin_site.admin_view(self.followup),
                                   name='foia-admin-followup'),
                               url(r'^send_update/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.send_update),
                                   name='foia-admin-send-update'))
        return my_urls + urls

    def _list_helper(self, request, foias, action):
        """List all the requests that need to be processed"""
        # pylint: disable-msg=R0201
        foias.sort(cmp=lambda x, y: cmp(x.communications.latest('date').date,
                                        y.communications.latest('date').date))
        return simple.direct_to_template(request, template='foia/admin_process.html',
                                         extra_context={'object_list': foias, 'action': action})

    def process(self, request):
        """List all the requests that need to be processed"""
        # pylint: disable-msg=R0201
        foias = list(FOIARequest.objects.filter(status='submitted'))
        return self._list_helper(request, foias, 'Process')

    def followup(self, request):
        """List all the requests that need to be followed up"""
        # pylint: disable-msg=R0201
        foias = list(FOIARequest.objects.get_followup())
        return self._list_helper(request, foias, 'Follow Up')

    def send_update(self, request, idx):
        """Manually send the user an update notification"""
        # pylint: disable-msg=R0201

        foia = get_object_or_404(FOIARequest, pk=idx)
        foia.updated()
        messages.info(request, 'An update notification has been set to the user, %s' % foia.user)
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[foia.pk]))


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
    list_filter = ['approved', 'jurisdiction', 'types']


admin.site.register(FOIARequest,  FOIARequestAdmin)
admin.site.register(FOIADocument, FOIADocumentAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
admin.site.register(AgencyType,   AgencyTypeAdmin)
admin.site.register(Agency,       AgencyAdmin)
admin.site.register(FOIADocTopViewed)
