"""
Admin registration for organization models
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from reversion import VersionAdmin
import autocomplete_light

from muckrock.organization.models import Organization

class OrganizationAdminForm(forms.ModelForm):
    """Agency admin form to order users"""
    owner = autocomplete_light.ModelChoiceField(
        'UserAdminAutocomplete',
        queryset=User.objects.all(),
        required=False
    )
    
    class Meta:
        # pylint: disable=R0903
        model = Organization

class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner')
    form = OrganizationAdminForm

admin.site.register(Organization, OrganizationAdmin)

