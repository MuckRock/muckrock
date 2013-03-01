"""
Admin registration for Agency models
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from adaptor.model import CsvModel
from adaptor.fields import CharField, DjangoModelField

from agency.models import AgencyType, Agency
from jurisdiction.models import Jurisdiction

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

admin.site.register(AgencyType, AgencyTypeAdmin)
admin.site.register(Agency,     AgencyAdmin)


class AgencyCsvModel(CsvModel):
    """CSV import model for agency"""

    @staticmethod
    def get_jurisdiction(full_name):
        """Get the jurisdiction from its name and parent"""
        # pylint: disable=E1101
        name, parent_abbrev = full_name.split(', ')
        parent = Jurisdiction.objects.get(abbrev=parent_abbrev)
        return Jurisdiction.objects.get(name=name, parent=parent).pk

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
