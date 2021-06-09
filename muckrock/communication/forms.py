"""Forns for communication application"""

# Django
from django import forms

# Third Party
from localflavor.us.forms import USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

# MuckRock
from muckrock.communication.models import Address, Check


class AddressForm(forms.ModelForm):
    """A form for entering an address"""

    # Character limits are for conforming to Lob's requirements
    agency_override = forms.CharField(
        max_length=40,
        label="Name",
        required=False,
        help_text="Who the letter should be addressed to.  If left blank, will default "
        "to the agency's name.  This should be filled in if the agency name "
        "is greater than 40 characters for Lob compatibility",
    )
    attn_override = forms.CharField(
        max_length=40,
        label="Attention of",
        required=False,
        help_text="Who the letter should be to the attention of.  If left blank, "
        "will default to the FOIA Office (or applicable law for states).",
    )
    street = forms.CharField(max_length=64)
    suite = forms.CharField(max_length=64, required=False)
    city = forms.CharField(max_length=200)
    state = forms.ChoiceField(choices=(("", "---"),) + tuple(STATE_CHOICES))
    zip_code = USZipCodeField()

    class Meta:
        model = Address
        fields = [
            "agency_override",
            "attn_override",
            "street",
            "suite",
            "city",
            "state",
            "zip_code",
        ]

    def __init__(self, *args, **kwargs):
        self.agency = kwargs.pop("agency")
        super(AddressForm, self).__init__(*args, **kwargs)

    def clean_agency_override(self):
        """Require this field if the agency name is too long"""
        agency_override = self.cleaned_data["agency_override"]
        if (
            not agency_override
            and not self.agency.mail_name
            and len(self.agency.name) > 40
        ):
            raise forms.ValidationError(
                "Must supply a name since the agency name is over 40 characters long"
            )
        return agency_override


class CheckDateForm(forms.ModelForm):
    """Form to set the deposit date for a check"""

    deposit_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%m/%d/%Y", attrs={"placeholder": "mm/dd/yyyy", "form": "check-form"}
        ),
        input_formats=[
            "%Y-%m-%d",  # '2006-10-25'
            "%m/%d/%Y",  # '10/25/2006'
            "%m/%d/%y",  # '10/25/06'
        ],
    )

    class Meta:
        model = Check
        fields = ["deposit_date"]
