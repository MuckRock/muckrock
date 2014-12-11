"""Forms for Jurisdiction application"""

from django import forms

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
