"""
Forms for Crowdfund application
"""

from django import forms

from muckrock.accounts.forms import PaymentForm
from muckrock.fields import USDCurrencyField

class CrowdfundEnableForm(forms.Form):
    """Form to confirm enable crowdfunding on a FOIA"""

    confirm = forms.BooleanField(label='Are you sure you want to enable crowdfunding on this '
                                       'FOIA request?')


class CrowdfundPayForm(PaymentForm):
    """Form to pay for crowdfunding"""
    # pylint: disable=R0901

    amount = USDCurrencyField()
