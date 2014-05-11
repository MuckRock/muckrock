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

    confirm = forms.BooleanField(label='Are you sure you want to enable crowdfunding on this '
                                       'FOIA request?')


class CrowdfundPayForm(PaymentForm):
    """Form to pay for crowdfunding"""
    # pylint: disable=R0901, too-few-public-methods

    def __init__(self, *args, **kwargs):
        super(CrowdfundPayForm, self).__init__(*args, **kwargs)

        # don't offer to save cc's for anonymous users
        if self.request.user.is_authenticated():
            del self.fields['email']
        else:
            del self.fields['save_cc']

    amount = USDCurrencyField(validators=[MinValueValidator(Decimal("0.5"))])
    email = forms.EmailField(help_text='For the receipt')
    display_name = forms.CharField(max_length=255, required=False,
                                  help_text='Name to display on site')
    show = forms.BooleanField(label='Show on site', required=False,
        help_text='Would you like your contribution to be made public?')
