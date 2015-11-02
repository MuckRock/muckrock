"""
Admin registration for Agency models
"""

from django import forms
from django.conf.urls import patterns, url
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.shortcuts import render_to_response, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext

from adaptor.model import CsvModel
from adaptor.fields import CharField, DjangoModelField
from reversion import VersionAdmin
import autocomplete_light
import logging
import sys

from muckrock.agency.models import AgencyType, Agency
from muckrock.agency.forms import CSVImportForm
from muckrock.jurisdiction.models import Jurisdiction

logger = logging.getLogger(__name__)

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods

class AgencyTypeAdmin(VersionAdmin):
    """AgencyType admin options"""
    list_display = ('name', )
    search_fields = ['name']


class AgencyAdminForm(forms.ModelForm):
    """Agency admin form to order users"""
    user = autocomplete_light.ModelChoiceField(
            'UserAutocomplete',
            queryset=User.objects.all(),
            required=False)
    jurisdiction = autocomplete_light.ModelChoiceField(
            'JurisdictionAdminAutocomplete',
            queryset=Jurisdiction.objects.all())
    appeal_agency = autocomplete_light.ModelChoiceField(
            'AgencyAdminAutocomplete',
            queryset=Agency.objects.all(),
            required=False)
    parent = autocomplete_light.ModelChoiceField(
            'AgencyAdminAutocomplete',
            queryset=Agency.objects.all(),
            required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Agency
        fields = '__all__'


class AgencyAdmin(VersionAdmin):
    """Agency admin options"""
    change_list_template = 'admin/agency/agency/change_list.html'
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'jurisdiction')
    list_filter = ['status', 'types']
    search_fields = ['name']
    filter_horizontal = ('types',)
    form = AgencyAdminForm
    formats = ['xls', 'csv']

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(AgencyAdmin, self).get_urls()
        my_urls = patterns('', url(r'^import/$', self.admin_site.admin_view(self.csv_import),
                                   name='agency-admin-import'))
        return my_urls + urls

    def csv_import(self, request):
        """Import a CSV file of agencies"""
        # pylint: disable=no-self-use
        # pylint: disable=broad-except

        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    agencies = AgencyCsvModel.import_data(data=request.FILES['csv_file'],
                                                          extra_fields=['True'])
                    messages.success(request, 'CSV - %d agencies imported' % len(agencies))
                except Exception as exc:
                    messages.error(request, 'ERROR: %s' % str(exc))
                    logger.error('Import error: %s', exc, exc_info=sys.exc_info())
                else:
                    if form.cleaned_data['type_']:
                        for agency in agencies:
                            agency.object.types.add(form.cleaned_data['type_'])
                    for agency in agencies:
                        aobj = agency.object
                        if not aobj.slug:
                            aobj.slug = slugify(aobj.name)
                            aobj.save()
                return redirect('admin:agency_agency_changelist')
        else:
            form = CSVImportForm()

        fields = ['name', 'slug', 'jurisdiction ("Boston, MA")', 'address', 'email', 'other_emails',
                  'contact first name', 'contact last name', 'contact_title', 'url', 'phone', 'fax']
        return render_to_response('admin/agency/import.html', {'form': form, 'fields': fields},
                                  context_instance=RequestContext(request))


admin.site.register(AgencyType, AgencyTypeAdmin)
admin.site.register(Agency, AgencyAdmin)


def get_jurisdiction(full_name):
    """Get the jurisdiction from its name and parent"""
    # pylint: disable=no-member
    if ', ' in full_name:
        name, parent_abbrev = full_name.split(', ')
        parent = Jurisdiction.objects.get(abbrev=parent_abbrev)
        return Jurisdiction.objects.get(name=name, parent=parent).pk
    else:
        return Jurisdiction.objects.exclude(level='l').get(name=full_name).pk

class EmailValidator(object):
    """Class to validate emails"""
    def validate(self, value):
        # pylint: disable=no-self-use
        """Must be blank or an email"""
        if value == '':
            return True
        # validate email will throw a validation error on failure
        validate_email(value)
        return True

class AgencyCsvModel(CsvModel):
    """CSV import model for agency"""

    name = CharField()
    slug = CharField()
    jurisdiction = DjangoModelField(Jurisdiction, prepare=get_jurisdiction)
    address = CharField()
    email = CharField(validator=EmailValidator)
    other_emails = CharField()
    contact_first_name = CharField()
    contact_last_name = CharField()
    contact_title = CharField()
    url = CharField()
    phone = CharField()
    fax = CharField()
    status = CharField()

    class Meta:
        # pylint: disable=too-few-public-methods
        dbModel = Agency
        delimiter = ','
        update = {'keys': ['name', 'jurisdiction']}
