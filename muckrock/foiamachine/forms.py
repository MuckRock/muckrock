"""
Forms for FOIA Machine
"""

from django import forms

from muckrock.foiamachine.models import FoiaMachineRequest

class FoiaMachineRequestForm(forms.ModelForm):
    """The FOIA Machine Request form provides a basis for creating and updating requests."""
    class Meta:
        model = FoiaMachineRequest
        fields = ['title', 'request_language', 'jurisdiction', 'agency']

    def clean(self):
        cleaned_data = super(FoiaMachineRequestForm, self).clean()
        jurisdiction = cleaned_data.get('jurisdiction')
        agency = cleaned_data.get('agency')
        if agency and agency.jurisdiction != jurisdiction:
            raise forms.ValidationError('This agency does not belong to the jurisdiction.')
        return cleaned_data
