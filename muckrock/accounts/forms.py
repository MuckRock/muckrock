"""
Forms for accounts application
"""

# Django
from django import forms

# Standard Library
import logging

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.organization.forms import StripeForm

logger = logging.getLogger(__name__)


class EmailSettingsForm(forms.ModelForm):
    """A form for updating user email preferences."""

    class Meta:
        model = Profile
        fields = ["email_pref", "use_autologin"]


class OrgPreferencesForm(forms.ModelForm):
    """A form for updating user organization preferences"""

    class Meta:
        model = Profile
        fields = ["org_share", "private_profile"]


class BuyRequestForm(StripeForm):
    """Form for buying more requests"""

    num_requests = forms.IntegerField(label="Number of requests to buy", min_value=1)

    def __init__(self, *args, **kwargs):
        super(BuyRequestForm, self).__init__(*args, **kwargs)
        if self._user.is_authenticated and self._user.profile.is_advanced():
            limit_val = 1
        else:
            limit_val = 4
        self.fields["num_requests"].validators[0].limit_value = limit_val
        self.fields["num_requests"].widget.attrs["min"] = limit_val
        self.fields["num_requests"].initial = limit_val


class ContactForm(forms.Form):
    """A form for contacting the user"""

    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea)
