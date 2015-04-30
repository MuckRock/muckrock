"""Forms for Agency application"""

from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField

from muckrock.agency.models import Agency, AgencyType
from muckrock.fields import FullEmailField


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    email = FullEmailField(required=False)
    phone = USPhoneNumberField(required=False)
    fax = USPhoneNumberField(required=False)

    class Meta:
        # pylint: disable=R0903
        model = Agency
        fields = ['name', 'aliases', 'address', 'email', 'url', 'phone', 'fax']

class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
    type_ = forms.ModelChoiceField(queryset=AgencyType.objects.all(), required=False)
