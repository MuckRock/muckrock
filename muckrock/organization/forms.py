"""
Forms for the organization application
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify

from muckrock.organization.models import Organization
from muckrock.settings import ORG_MIN_SEATS

import autocomplete_light

class CreateForm(forms.ModelForm):
    """Allows ordinary users to create an organization"""
    class Meta:
        model = Organization
        fields = ['name']

    def clean_name(self):
        """Ensures name is unique"""
        name = self.cleaned_data['name']
        slug = slugify(name)
        try:
            Organization.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return name
        raise forms.ValidationError('Organization already exists with this name.')


class StaffCreateForm(CreateForm):
    """Allows staff more control over the creation of an organization"""
    class Meta:
        model = Organization
        fields = ['name', 'owner', 'monthly_requests', 'monthly_cost', 'max_users']
        widgets = {'owner': autocomplete_light.ChoiceWidget('UserAutocomplete')}


class SeatForm(forms.ModelForm):
    """Allows setting the seats of the organization."""
    class Meta:
        model = Organization
        fields = ['max_users']

    def clean_max_users(self):
        """Ensures that max_users is not below the minimum value."""
        seats = self.cleaned_data['max_users']
        if seats < ORG_MIN_SEATS:
            err_msg = 'Organizations have a %d-seat minimum' % ORG_MIN_SEATS
            raise forms.ValidationError(err_msg)
        return seats


class AddMembersForm(forms.Form):
    """A form that uses autocomplete to suggest users to add to an organization"""
    add_members = forms.ModelMultipleChoiceField(
        required=True,
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserOrganizationAutocomplete')
    )
