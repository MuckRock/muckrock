"""
Forms for the organization application
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify

from muckrock.organization.models import Organization

import autocomplete_light

class OrganizationForm(forms.ModelForm):
    """A form for creating an Organization"""
    def clean_name(self):
        """Ensures name is unique"""
        name = self.cleaned_data['name']
        slug = slugify(name)
        try:
            Organization.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return name
        raise forms.ValidationError('Organization already exists with this name.')

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Organization
        fields = ['name', 'owner', 'monthly_requests', 'monthly_cost', 'max_users']
        widgets = {'owner': autocomplete_light.ChoiceWidget('UserAutocomplete')}

class OrganizationUpdateForm(forms.ModelForm):
    """A form for tweaking the number of members, number of reqeusts, and monthly cost"""
    class Meta:
        model = Organization
        fields = ['max_users', 'monthly_cost', 'monthly_requests']

class AddMembersForm(forms.Form):
    """A form that uses autocomplete to suggest users to add to an organization"""
    add_members = forms.ModelMultipleChoiceField(
        required=True,
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserOrganizationAutocomplete')
    )
