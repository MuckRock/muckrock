"""Forms for Agency application"""

from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField

from agency.models import Agency


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    phone = USPhoneNumberField(required=False)
    fax = USPhoneNumberField(required=False)

    class Meta:
        # pylint: disable=R0903
        model = Agency
        fields = ['name', 'jurisdiction', 'address', 'email', 'url', 'phone', 'fax']
        widgets = {'address': forms.Textarea(attrs={'style': 'width:250px; height:80px;'}),
                   'url': forms.TextInput(attrs={'style': 'width:250px;'})}


class FlagForm(forms.Form):
    """Form to flag an agency"""
    reason = forms.CharField(widget=forms.Textarea(attrs={'style': 'width:450px; height:200px;'}),
                             label='Reason')

    help_text = 'Submit a correction for an agency in order to let us know that something is ' \
                'wrong with it, such as providing missing information or correcting incorrect ' \
                'information.  Please describe the problem as specifically as possibly here:'
