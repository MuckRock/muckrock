"""
Forms for Crowdfund application
"""

from django import forms

from muckrock.crowdfund.models import CrowdfundRequest

class NumberInput(forms.TextInput):
    input_type = 'number'

class CrowdfundRequestForm(forms.ModelForm):
    """Form to confirm enable crowdfunding on a FOIA"""

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

    class Meta:
        model = CrowdfundRequest
        fields = ['name', 'description', 'payment_required', 'date_due', 'foia']
        widgets = {
            'foia': forms.HiddenInput()
        }
