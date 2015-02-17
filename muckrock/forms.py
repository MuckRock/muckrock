"""
Forms for MuckRock
"""

from django import forms
from django.contrib.auth.models import User

import autocomplete_light as autocomplete

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

class MRFilterForm(forms.Form):
    """A generic class to filter a list of items"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=autocomplete.ChoiceWidget('UserAutocomplete'))
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete.ChoiceWidget('AgencyAutocomplete'))
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete.ChoiceWidget('JurisdictionAutocomplete'))