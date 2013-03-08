"""Forms for Jurisdiction application"""

from django import forms

class FlagForm(forms.Form):
    """Form to flag an agency or jurisdiction"""
    reason = forms.CharField(widget=forms.Textarea(attrs={'style': 'width:450px; height:200px;'}),
                             label='Reason')

    help_text = 'Submit a correction for an agency or jurisdiction in order to let us know that ' \
                'something is wrong with it, such as providing missing information or correcting ' \
                'incorrect information.  Please describe the problem as specifically as possibly ' \
                'here:'


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
