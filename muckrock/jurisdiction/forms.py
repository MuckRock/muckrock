"""Forms for Jurisdiction application"""

from django import forms

from muckrock.forms import MRFilterForm
from muckrock.jurisdiction.models import Jurisdiction

from autocomplete_light import shortcuts as autocomplete_light

class JurisdictionFilterForm(MRFilterForm):
    """Adds a level filter to MRFilterForm"""
    levels = (
        ('f', 'Federal'),
        ('s', 'State'),
        ('l', 'Local'),
    )
    level = forms.ChoiceField(
        choices=levels,
        widget=forms.RadioSelect
    )
    parent = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'StateAutocomplete',
            attrs={'placeholder': 'All States'}))

class FlagForm(forms.Form):
    """Form to flag an agency or jurisdiction"""
    reason = forms.CharField(
        widget=forms.Textarea(),
        label='Submit a Change',
        help_text=(
            'Please describe the change, such as providing missing information '
            'or correcting existing information, in sufficient detail below:'
        )
    )


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
