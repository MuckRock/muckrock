"""
Forms for Crowdfund application
"""

from django import forms

from decimal import Decimal
from datetime import date, timedelta

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
        """Add fee to the total crowdfund amount, make sure it isn't zero"""
        amount = self.cleaned_data['payment_required']
        valid_amount = amount > 0
        if not valid_amount:
            raise forms.ValidationError('Amount to crowdfund must be greater than zero.')
        amount += amount * self.fee_rate
        return amount

    def clean_date_due(self):
        """Ensure date is not in the past"""
        deadline = self.cleaned_data['date_due']
        correct_duration = deadline > date.today()
        if not correct_duration:
            raise forms.ValidationError('Crowdfund deadline must be after today.')
        return deadline
