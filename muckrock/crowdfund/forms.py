"""
Forms for Crowdfund application
"""

from django import forms
from django.core.validators import MinValueValidator

from decimal import Decimal

from muckrock.accounts.forms import PaymentForm
from muckrock.fields import USDCurrencyField

class CrowdfundEnableForm(forms.Form):
    """Form to confirm enable crowdfunding on a FOIA"""
    label = 'Enable crowdfunding on this FOIA request?'
    confirm = forms.BooleanField(label=label)