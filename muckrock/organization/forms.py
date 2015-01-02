"""
Forms for the organization application
"""

from django import forms
from django.contrib.auth.models import User

from muckrock.organization.models import Organization

import autocomplete_light

class OrganizationForm(forms.ModelForm):
    """A form for an Agency"""

    class Meta:
        # pylint: disable=R0903
        model = Organization
        fields = ['name']

class AddMemberForm(forms.Form):
    add_members = forms.ModelMultipleChoiceField(
        required=True, 
        queryset=User.objects.all(), 
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
