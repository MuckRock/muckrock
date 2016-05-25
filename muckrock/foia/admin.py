"""
Admin registration for FOIA models
"""

from django import forms
from django.conf.urls import patterns, url
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from autocomplete_light import shortcuts as autocomplete_light
from datetime import date, datetime, timedelta
from reversion.admin import VersionAdmin

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, FOIAFile, FOIACommunication, \
                                 FOIANote, STATUS
from muckrock.foia.tasks import upload_document_cloud, set_document_cloud_pages, autoimport, \
                                submit_multi_request
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.nested_inlines.admin import NestedModelAdmin, NestedTabularInline

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods
# pylint: disable=bad-continuation

class FOIAFileAdminForm(forms.ModelForm):
    """Form to validate document only has ASCII characters in it"""

    def __init__(self, *args, **kwargs):
        super(FOIAFileAdminForm, self).__init__(*args, **kwargs)
        self.clean_title = self._validate('title')
        self.clean_source = self._validate('source')
        self.clean_description = self._validate('description')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIAFile
        fields = '__all__'

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


class FOIAFileInline(NestedTabularInline):
    """FOIA File Inline admin options"""
    model = FOIAFile
    form = FOIAFileAdminForm
    readonly_fields = ['doc_id', 'pages']
    exclude = ('foia', 'access', 'source')
    extra = 0


class FOIACommunicationInline(NestedTabularInline):
    """FOIA Communication Inline admin options"""
    model = FOIACommunication
    fk_name = 'foia'
    extra = 1
    readonly_fields = ['opened']
    exclude = ('likely_foia',)
    inlines = [FOIAFileInline]
    prefetch = 'files'


class FOIANoteInline(NestedTabularInline):
    """FOIA Notes Inline admin options"""
    model = FOIANote
    extra = 1


class FOIARequestAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    jurisdiction = autocomplete_light.ModelChoiceField('JurisdictionAdminAutocomplete',
                                                       queryset=Jurisdiction.objects.all())
    agency = autocomplete_light.ModelChoiceField('AgencyAdminAutocomplete',
                                                 queryset=Agency.objects.all())
    user = autocomplete_light.ModelChoiceField('UserAutocomplete',
                                               queryset=User.objects.all())
    parent = autocomplete_light.ModelChoiceField('FOIARequestAdminAutocomplete',
                                                 queryset=FOIARequest.objects.all(),
                                                 required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIARequest
        fields = '__all__'


class FOIARequestAdmin(NestedModelAdmin, VersionAdmin):
    """FOIA Request admin options"""
    change_list_template = 'admin/foia/foiarequest/change_list.html'
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status', 'agency', 'jurisdiction')
    list_filter = ['status']
    list_select_related = True
    search_fields = ['title', 'description', 'tracking_id', 'mail_id']
    readonly_fields = ['mail_id']
    filter_horizontal = ('read_collaborators', 'edit_collaborators')
    inlines = [FOIACommunicationInline, FOIANoteInline]
    save_on_top = True
    form = FOIARequestAdminForm
    formats = ['xls', 'csv']
    # pylint: disable=protected-access
    headers = [f.name for f in FOIARequest._meta.fields] + ['total_pages']

    def save_model(self, request, obj, form, change):
        """Actions to take when a request is saved from the admin"""

        # If changing to completed and embargoed, set embargo date to 30 days out
        if obj.status in ['done', 'partial'] and obj.embargo and not obj.date_embargo:
            obj.date_embargo = date.today() + timedelta(30)

        # NOT saving here if changed
        # saving after formset so that we can check for updates there first
        if not change:
            obj.save()


    def save_formset(self, request, form, formset, change):
        """Actions to take while saving inline instances"""

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

        # check communications and files for new ones to notify the user of an update
        instances = formset.save(commit=False)
        for instance in instances:
            # only way to tell if its new or not is to check the db
            change = True
            try:
                formset.model.objects.get(pk=instance.pk)
            except formset.model.DoesNotExist:
                change = False

            if formset.model == FOIAFile:
                instance.foia = instance.comm.foia

            instance.save()
            # its new, so notify the user about it
            if not change and formset.model == FOIACommunication:
                instance.foia.update(instance.anchor())
            if not change and formset.model == FOIAFile:
                instance.comm.foia.update(instance.anchor())

            if formset.model == FOIAFile:
                upload_document_cloud.apply_async(args=[instance.pk, change], countdown=30)

        formset.save_m2m()

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(FOIARequestAdmin, self).get_urls()
        my_urls = patterns('', url(r'^process/$', self.admin_site.admin_view(self.process),
                                   name='foia-admin-process'),
                               url(r'^followup/$', self.admin_site.admin_view(self.followup),
                                   name='foia-admin-followup'),
                               url(r'^undated/$', self.admin_site.admin_view(self.undated),
                                   name='foia-admin-undated'),
                               url(r'^send_update/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.send_update),
                                   name='foia-admin-send-update'),
                               url(r'^retry_pages/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.retry_pages),
                                   name='foia-admin-retry-pages'),
                               url(r'^set_status/(?P<idx>\d+)/(?P<status>\w+)/$',
                                   self.admin_site.admin_view(self.set_status),
                                   name='foia-admin-set-status'),
                               url(r'^autoimport/$',
                                   self.admin_site.admin_view(self.autoimport),
                                   name='foia-admin-autoimport'))
        return my_urls + urls

    def _list_helper(self, request, foias, action):
        """List all the requests that need to be processed"""
        # XXX do we use any of these any more?
        # pylint: disable=no-self-use
        paginator = Paginator(foias, 10)
        try:
            page = paginator.page(request.GET.get('page'))
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return render_to_response('admin/foia/admin_process.html',
                                  {'page': page, 'action': action},
                                  context_instance=RequestContext(request))

    def process(self, request):
        """List all the requests that need to be processed"""
        # pylint: disable=no-self-use
        foias = list(FOIARequest.objects.filter(status='submitted'))
        return self._list_helper(request, foias, 'Process')

    def followup(self, request):
        """List all the requests that need to be followed up"""
        # pylint: disable=no-self-use
        foias = list(FOIARequest.objects.get_manual_followup())
        return self._list_helper(request, foias, 'Follow Up')

    def undated(self, request):
        """List all the requests that have undated documents or files"""
        # pylint: disable=no-self-use
        foias = list(FOIARequest.objects.get_undated())
        return self._list_helper(request, foias, 'Undated')

    def send_update(self, request, idx):
        """Manually send the user an update notification"""
        # pylint: disable=no-self-use

        foia = get_object_or_404(FOIARequest, pk=idx)
        foia.update()
        messages.info(request, 'An update notification has been set to the user, %s' % foia.user)
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[foia.pk]))

    def retry_pages(self, request, idx):
        """Retry getting the page count"""
        # pylint: disable=no-self-use

        docs = FOIAFile.objects.filter(foia=idx, pages=0)
        for doc in docs:
            if doc.is_doccloud():
                set_document_cloud_pages.apply_async(args=[doc.pk])

        messages.info(request, 'Attempting to set the page count for %d documents... Please '
                               'wait while the Document Cloud servers are being accessed'
                               % docs.count())
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[idx]))

    def autoimport(self, request):
        """Autoimport documents from S3"""
        # pylint: disable=no-self-use
        autoimport.apply_async()
        messages.info(request, 'Auotimport started')
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_changelist'))

    def set_status(self, request, idx, status):
        """Set the status of the request"""
        # pylint: disable=no-self-use

        try:
            foia = FOIARequest.objects.get(pk=idx)
        except FOIARequest.DoesNotExist:
            messages.error(request, '%s is not a valid FOIA Request' % idx)
            return HttpResponseRedirect(reverse('admin:foia_foiarequest_changelist'))

        if status not in [s for (s, _) in STATUS]:
            messages.error(request, '%s is not a valid status' % status)
            return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[foia.pk]))

        foia.status = status
        foia.update()
        dateord = request.GET.get('dateord')
        if status in ['rejected', 'no_docs', 'done', 'abandoned'] and dateord:
            foia.date_done = date.fromordinal(int(dateord))
        foia.save()
        last_comm = foia.last_comm()
        last_comm.status = status
        last_comm.save()

        try:
            if status in ['ack', 'processed', 'appealing']:
                comm_pk = request.GET.get('comm_pk')
                comm = FOIACommunication.objects.get(pk=comm_pk)
                if comm.foia == foia:
                    comm.date = datetime.now()
                    comm.save()
        except FOIACommunication.DoesNotExist:
            pass

        messages.success(request, 'Status set to %s' % foia.get_status_display())
        return HttpResponseRedirect(reverse('admin:foia_foiarequest_change', args=[foia.pk]))


class FOIAMultiRequestAdmin(VersionAdmin):
    """FOIA Multi Request admin options"""
    change_form_template = 'admin/foia/multifoiarequest/change_form.html'
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'status')
    search_fields = ['title', 'requested_docs']
    filter_horizontal = ['agencies']

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(FOIAMultiRequestAdmin, self).get_urls()
        my_urls = patterns('', url(r'^submit/(?P<idx>\d+)/$',
                                   self.admin_site.admin_view(self.submit),
                                   name='multifoia-admin-submit'))
        return my_urls + urls

    def submit(self, request, idx):
        """Submit the multi request"""
        # pylint: disable=no-self-use

        get_object_or_404(FOIAMultiRequest, pk=idx)
        submit_multi_request.apply_async(args=[idx])

        messages.info(request, 'Multi request is being submitted...')
        return HttpResponseRedirect(reverse('admin:foia_foiamultirequest_changelist'))


admin.site.register(FOIARequest, FOIARequestAdmin)
admin.site.register(FOIAMultiRequest, FOIAMultiRequestAdmin)
