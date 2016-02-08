"""
Forms for the organization application
"""

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify

from muckrock.organization.models import Organization

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

    def clean_max_users(self):
        """Ensures that max_users is not below the minimum value."""
        max_users = self.cleaned_data['max_users']
        if max_users < settings.ORG_MIN_SEATS:
            err_msg = 'Organizations have a %d-seat minimum' % settings.ORG_MIN_SEATS
            raise forms.ValidationError(err_msg)
        return max_users


class UpdateForm(forms.ModelForm):
    """Allows owner to update the number of seats in their organization."""
    class Meta:
        model = Organization
        fields = ['max_users']
        widgets = {'max_users': forms.NumberInput(attrs={'min': settings.ORG_MIN_SEATS})}
        labels = {'max_users': 'Member Seats'}

    def clean_max_users(self):
        """Ensures that max_users is not below the minimum value."""
        max_users = self.cleaned_data['max_users']
        if max_users < settings.ORG_MIN_SEATS:
            err_msg = 'Organizations have a %d-seat minimum' % settings.ORG_MIN_SEATS
            raise forms.ValidationError(err_msg)
        if max_users < self.instance.members.count():
            err_msg = ('Organizations cannot have fewer seats than members. ' +
                       'Please remove members first.')
            raise forms.ValidationError(err_msg)
        return max_users


class StaffUpdateForm(UpdateForm):
    """Allows staff more control over the updating of an organization"""
    class Meta:
        model = Organization
        fields = ['monthly_requests', 'monthly_cost', 'max_users']


class AddMembersForm(forms.Form):
    """A form that uses autocomplete to suggest users to add to an organization"""
    members = forms.ModelMultipleChoiceField(
        required=True,
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserOrganizationAutocomplete')
    )
