"""
Admin registration for FOIA models
"""

from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import simple

from datetime import date, timedelta

from foia.models import FOIARequest, FOIADocument, FOIAFile, FOIACommunication, FOIANote
from muckrock.foia.tasks import upload_document_cloud, set_document_cloud_pages

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class FOIADocumentAdminForm(forms.ModelForm):
    """Form to validate document only has ASCII characters in it"""

    def __init__(self, *args, **kwargs):
        super(FOIADocumentAdminForm, self).__init__(*args, **kwargs)
        self.clean_title = self._validate('title')
        self.clean_source = self._validate('source')
        self.clean_description = self._validate('description')

    class Meta:
        # pylint: disable=R0903
        model = FOIADocument

    @staticmethod
    def _only_ascii(text):
        """Ensure's that text only contains ASCII characters"""
        non_ascii = ''.join(c for c in text if ord(c) >= 128)
        if non_ascii:
            raise forms.ValidationError('Field contains non-ASCII characters: %s' % non_ascii)

    def _validate(self, field):
        """Make a validator for field"""

        def inner():
            """Ensure field only has ASCII characters"""
            data = self.cleaned_data[field]
            self._only_ascii(data)
            return data

        return inner


class FOIADocumentInline(admin.TabularInline):
    """FOIA Document Inline admin options"""
    model = FOIADocument
    form = FOIADocumentAdminForm
    readonly_fields = ['doc_id', 'pages']
    extra = 2


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
    inlines = [FOIACommunicationInline, FOIADocumentInline, FOIAFileInline, FOIANoteInline]
    save_on_top = True

    def save_model(self, request, obj, form, change):
        """Actions to take when a request is saved from the admin"""

        # If changing to completed and embargoed, set embargo date to 30 days out
        if obj.status in ['done', 'partial'] and obj.embargo and not obj.date_embargo:
            obj.date_embargo = date.today() + timedelta(30)

        # NOT saving here - saving after formset so that we can check for updates there first

    def save_formset(self, request, form, formset, change):
        """Actions to take while saving inline instances"""
        # pylint: disable=E1101

        if formset.model == FOIANote:
            formset.save()
            # check for foia updates here so that communication updates take priority
            # (Notes are last)
            foia = form.instance
            old_foia = FOIARequest.objects.get(pk=foia.pk)
            if foia.status != old_foia.status:
                foia.update()
            foia.update_dates()
            foia.save()
            return

        # check communications, files, and docs for new ones to notify the user of an update
        instances = formset.save(commit=False)
        for instance in instances:
            # only way to tell if its new or not is to check the db
            change = True
            try:
                formset.model.objects.get(pk=instance.pk)
            except formset.model.DoesNotExist:
                change = False

            instance.save()
            if not change:
                # its new, so notify the user about it
                instance.foia.update(instance.anchor())
            if formset.model == FOIADocument:
                upload_document_cloud.apply_async(args=[instance.pk, change], countdown=3)

        formset.save_m2m()


    def get_urls(self):
        """Add custom URLs here"""
        urls = super(FOIARequestAdmin, self).get_urls()
        my_urls = patterns('', url(r'^process/$', self.admin_site.admin_view(self.process),
                                   name='foia-admin-process'),
                               url(r'^followup/$', self.admin_site.admin_view(self.followup),
                                   name='foia-admin-followup'),
                               url(r'^send_update/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.send_update),
                                   name='foia-admin-send-update'),
                               url(r'^retry_pages/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.retry_pages),
                                   name='foia-admin-retry-pages'))
        return my_urls + urls

    def _list_helper(self, request, foias, action):
        """List all the requests that need to be processed"""
        # pylint: disable=R0201
        foias.sort(cmp=lambda x, y: cmp(x.communications.latest('date').date,
                                        y.communications.latest('date').date))
        return simple.direct_to_template(request, template='foia/admin_process.html',
                                         extra_context={'object_list': foias, 'action': action})

    def process(self, request):
        """List all the requests that need to be processed"""
        # pylint: disable=R0201
        foias = list(FOIARequest.objects.filter(status='submitted'))
        return self._list_helper(request, foias, 'Process')

    def followup(self, request):
        """List all the requests that need to be followed up"""
        # pylint: disable=R0201
        foias = list(FOIARequest.objects.get_followup())
        return self._list_helper(request, foias, 'Follow Up')

    def send_update(self, request, idx):
        """Manually send the user an update notification"""
        # pylint: disable=R0201

        foia = get_object_or_404(FOIARequest, pk=idx)
        foia.update()
        messages.info(request, 'An update notification has been set to the user, %s' % foia.user)
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[foia.pk]))

    def retry_pages(self, request, idx):
        """Retry getting the page count"""
        # pylint: disable=E1101
        # pylint: disable=R0201

        docs = FOIADocument.objects.filter(foia=idx, pages=0)
        for doc in docs:
            set_document_cloud_pages.apply_async(args=[doc.pk])

        messages.info(request, 'Attempting to set the page count for %d documents... Please '
                               'wait while the Document Cloud servers are being accessed'
                               % docs.count())
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[idx]))


admin.site.register(FOIARequest,  FOIARequestAdmin)
