"""
Forms for Crowdfund application
"""

from django import forms

from decimal import Decimal, ROUND_DOWN, InvalidOperation
from datetime import date, timedelta

from muckrock.crowdfund.models import Crowdfund


class NumberInput(forms.TextInput):
    """Patches a NumberInput widget on top of the TextInput widget"""
    input_type = 'number'


class CrowdfundForm(forms.ModelForm):
    """Form to confirm enable crowdfunding"""

    fee_rate = 0.15

    class Meta:
        model = Crowdfund
        fields = [
            'name',
            'description',
            'payment_required',
            'payment_capped',
            'date_due',
        ]

    payment_required = forms.IntegerField(
        label='Amount',
        help_text='We will add 15% to this amount, which goes towards our operating costs.',
        widget=NumberInput(attrs={'class': 'currency-field'})
    )

    payment_capped = forms.BooleanField(
        label='Limit Amount',
        required=False,
        help_text='If checked, this prevents you from collecting more than your stated amount.',
        widget=forms.CheckboxInput()
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
        # since the amount we get should always be a 1-cent relative integer
        # (e.g. $1.00 = 100), we should normalize the amount into a decimal value
        amount = Decimal(amount)/100
        return amount.quantize(Decimal('.01'), rounding=ROUND_DOWN)

    def clean_date_due(self):
        """Ensure date is not in the past"""
        deadline = self.cleaned_data['date_due']
        today = date.today()
        after_today = deadline > today
        if not after_today:
            raise forms.ValidationError('Crowdfund deadline must be after today.')
        lte_30_days = deadline - today <= timedelta(30)
        if not lte_30_days:
            raise forms.ValidationError('Crowdfund duration cannot exceed 30 days.')
        return deadline


class CrowdfundPaymentForm(forms.Form):
    """Form to create a payment to a crowdfund"""
    stripe_amount = forms.CharField(widget=NumberInput())
    show = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    crowdfund = forms.ModelChoiceField(queryset=Crowdfund.objects.all(), widget=forms.HiddenInput())
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your Full Name'})
    )
    recurring = forms.BooleanField(required=False)

    def clean_stripe_amount(self):
        """Ensure the amount of the payment is greater than zero"""
        amount = self.cleaned_data['stripe_amount']
        if not amount > 0:
            raise forms.ValidationError('Cannot contribute zero dollars')
        try:
            amount = Decimal(amount)/100
        except InvalidOperation:
            raise forms.ValidationError('Invalid amount')
        return amount
