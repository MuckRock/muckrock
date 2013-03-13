"""
Admin registration for Jurisdiction models
"""

from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.shortcuts import render_to_response, redirect

from adaptor.model import CsvModel
from adaptor.fields import CharField, DjangoModelField
from django_tablib.admin import TablibAdmin

#from jurisdiction.models import Jurisdiction
from foia.models import Jurisdiction
from jurisdiction.forms import CSVImportForm

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class JurisdictionAdmin(TablibAdmin):
    """Jurisdiction admin options"""
    change_list_template = 'admin/jurisdiction/jurisdiction/change_list.html'
    list_display = ('name', 'level')
    list_filter = ['level']
    search_fields = ['name']
    filter_horizontal = ('holidays', )
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'abbrev', 'level', 'parent', 'hidden', 'image',
                       'image_attr_line', 'public_notes')
        }),
        ('Options for states/federal', {
            'classes': ('collapse',),
            'fields': ('days', 'observe_sat', 'holidays', 'intro', 'waiver')
        }),
    )
    formats = ['xls', 'csv']

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(JurisdictionAdmin, self).get_urls()
        my_urls = patterns('', url(r'^import/$', self.admin_site.admin_view(self.csv_import),
                                   name='jurisdiction-admin-import'))
        return my_urls + urls

    def csv_import(self, request):
        """Import a CSV file of jurisdictions"""
        # pylint: disable=R0201

        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                JurisdictionCsvModel.import_data(data=request.FILES['csv_file'])
                messages.success(request, 'CSV imported')
                return redirect('admin:jurisdiction_jurisdiction_changelist')
        else:
            form = CSVImportForm()

        fields = ['name', 'slug', 'level', 'parent']
        return render_to_response('admin/agency/import.html', {'form': form, 'fields': fields})

admin.site.register(Jurisdiction, JurisdictionAdmin)


class JurisdictionCsvModel(CsvModel):
    """CSV import model for jurisdictions"""

    name = CharField()
    slug = CharField()
    level = CharField(transform=lambda x: x.lower()[0])
    parent = DjangoModelField(Jurisdiction, pk='name')

    class Meta:
        # pylint: disable=R0903
        dbModel = Jurisdiction
        delimiter = ','
        update = {'keys': ['slug', 'parent']}
