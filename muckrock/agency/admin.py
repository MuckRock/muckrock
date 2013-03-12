"""
Admin registration for Agency models
"""

from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, redirect

from adaptor.model import CsvModel
from adaptor.fields import CharField, DjangoModelField

from muckrock.agency.models import AgencyType, Agency
from muckrock.agency.forms import CSVImportForm
from muckrock.jurisdiction.models import Jurisdiction

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class AgencyTypeAdmin(admin.ModelAdmin):
    """AgencyType admin options"""
    list_display = ('name', )
    search_fields = ['name']


class AgencyAdminForm(forms.ModelForm):
    """Agency admin form to order users"""
    user = forms.models.ModelChoiceField(queryset=User.objects.all().order_by('username'))

    class Meta:
        # pylint: disable=R0903
        model = Agency


class AgencyAdmin(admin.ModelAdmin):
    """Agency admin options"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'jurisdiction')
    list_filter = ['approved', 'jurisdiction', 'types']
    search_fields = ['name']
    form = AgencyAdminForm

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(AgencyAdmin, self).get_urls()
        my_urls = patterns('', url(r'^import/$', self.admin_site.admin_view(self.csv_import),
                                   name='agency-admin-import'))
        return my_urls + urls

    def csv_import(self, request):
        """Import a CSV file of agencies"""
        # pylint: disable=R0201

        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                agencies = AgencyCsvModel.import_data(data=request.FILES['csv_file'])
                messages.success(request, 'CSV imported')
                if form.cleaned_data['type_']:
                    for agency in agencies:
                        agency.object.types.add(form.cleaned_data['type_'])
                return redirect('admin:agency_agency_changelist')
        else:
            form = CSVImportForm()

        fields = ['name', 'slug', 'jurisdiction ("Boston, MA")', 'address', 'email',
                  'contact first name', 'contact last name', 'url', 'phone', 'fax']
        return render_to_response('admin/agency/import.html', {'form': form, 'fields': fields})


admin.site.register(AgencyType, AgencyTypeAdmin)
admin.site.register(Agency,     AgencyAdmin)


def get_jurisdiction(full_name):
    """Get the jurisdiction from its name and parent"""
    # pylint: disable=E1101
    name, parent_abbrev = full_name.split(', ')
    parent = Jurisdiction.objects.get(abbrev=parent_abbrev)
    return Jurisdiction.objects.get(name=name, parent=parent).pk


class AgencyCsvModel(CsvModel):
    """CSV import model for agency"""

    name = CharField()
    slug = CharField()
    jurisdiction = DjangoModelField(Jurisdiction, prepare=get_jurisdiction)
    address = CharField()
    email = CharField()
    contact_first_name = CharField()
    contact_last_name = CharField()
    contact_title = CharField()
    url = CharField()
    phone = CharField()
    fax = CharField()

    class Meta:
        # pylint: disable=R0903
        dbModel = Agency
        delimiter = ','
        update = {'keys': ['name', 'jurisdiction']}
