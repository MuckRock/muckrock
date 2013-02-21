"""
Admin registration for Agency models
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from agency.models import AgencyType, Agency

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
