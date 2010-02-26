"""
Forms for FOIA application
"""

from django import forms
from foia.models import FOIARequest

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'jurisdiction', 'agency', 'request']

