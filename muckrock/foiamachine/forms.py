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
