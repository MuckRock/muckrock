"""
Forms for Crowdfund application
"""

from django import forms

from decimal import Decimal

from muckrock.crowdfund.models import CrowdfundRequest

class NumberInput(forms.TextInput):
    input_type = 'number'

class CrowdfundRequestForm(forms.ModelForm):
    """Form to confirm enable crowdfunding on a FOIA"""

    fee_rate = Decimal(0.1)

    class Meta:
        model = CrowdfundRequest
        fields = ['name', 'description', 'payment_required', 'date_due', 'foia']
        widgets = {
            'foia': forms.HiddenInput()
        }

    payment_required = forms.DecimalField(
        label='Amount',
        help_text='We will add 10% to this amount, which goes towards our operating costs.',
        widget=NumberInput()
    )

    date_due = forms.DateField(
        label='Deadline',
        help_text='Crowdfunding campaigns are limited to a maximum duration of 30 days',
        widget=forms.DateInput()
    )

    def clean_payment_required(self):
        """Add fee to the total crowdfund amount"""
        amount = self.cleaned_data['payment_required']
        amount += amount * self.fee_rate
        return amount
