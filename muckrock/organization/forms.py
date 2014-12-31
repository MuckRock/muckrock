"""
Forms for the organization application
"""

from django import forms
from django.contrib.auth.models import User

import autocomplete_light

class AddMemberForm(forms.Form):
    add_members = forms.ModelChoiceField(
        required=True, 
        queryset=User.objects.all(), 
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
