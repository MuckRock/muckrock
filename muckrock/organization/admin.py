"""
Admin registration for organization models
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.organization.models import Organization


class OrganizationAdminForm(forms.ModelForm):
    """Agency admin form to order users"""
    owner = autocomplete_light.ModelChoiceField(
        'UserAutocomplete',
        queryset=User.objects.all(),
        required=False
    )

    def clean_owner(self):
        """Ensures name is unique"""
        owner = self.cleaned_data['owner']
        if not owner:
            raise forms.ValidationError('Organization must have an owner.')
        return owner

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Organization
        fields = '__all__'


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner')
    form = OrganizationAdminForm


admin.site.register(Organization, OrganizationAdmin)
