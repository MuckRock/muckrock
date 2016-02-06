"""Forms for Agency application"""

from django import forms

from localflavor.us.forms import USPhoneNumberField

from muckrock.agency.models import Agency, AgencyType
from muckrock.fields import FullEmailField


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    email = FullEmailField(required=False)
    phone = USPhoneNumberField(required=False)
    fax = USPhoneNumberField(required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Agency
        fields = ['name', 'aliases', 'address', 'email', 'url', 'phone', 'fax']
        labels = {
            'aliases': 'Alias',
            'url': 'Website',
            'address': 'Mailing Address'
        }
        help_texts = {
            'aliases': ('An alternate name for the agency, '
                        'e.g. "CIA" is an alias for "Central Intelligence Agency".')
        }


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
    type_ = forms.ModelChoiceField(queryset=AgencyType.objects.all(), required=False)
