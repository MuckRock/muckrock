"""
Forms for the organization application
"""

from django import forms
from django.contrib.auth.models import User

from muckrock.organization.models import Organization

import autocomplete_light

class OrganizationForm(forms.ModelForm):
    """A form for creating an Organization"""
    class Meta:
        # pylint: disable=R0903
        model = Organization
        fields = ['name']

class AddMembersForm(forms.Form):
    """A form that uses autocomplete to suggest users to add to an organization"""
    add_members = forms.ModelMultipleChoiceField(
        required=True,
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserOrganizationAutocomplete')
    )
