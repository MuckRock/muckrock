"""
Forms for MuckRock
"""

from django import forms
from django.contrib.auth.models import User

import autocomplete_light as autocomplete
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

class MRFilterForm(forms.Form):
    """A generic class to filter a list of items"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=autocomplete.ChoiceWidget(
            'UserAutocomplete',
            attrs={'placeholder': 'All Users'}))
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete.ChoiceWidget(
            'AgencyAutocomplete',
            attrs={'placeholder': 'All Agencies'}))
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete.ChoiceWidget(
            'JurisdictionAutocomplete',
            attrs={'placeholder': 'All Jurisdictions'}))
    tags = TaggitField(widget=TaggitWidget(
        'TagAutocomplete',
        attrs={'placeholder': 'All Tags', 'data-autocomplete-minimum-characters': 1}))
