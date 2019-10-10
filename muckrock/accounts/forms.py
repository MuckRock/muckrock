"""
Forms for accounts application
"""

# Django
from django import forms

# Standard Library
import logging

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.organization.forms import OrganizationChoiceField, StripeForm
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)


class ProfileSettingsForm(forms.ModelForm):
    """A form for updating user information"""
    location = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget('JurisdictionLocalAutocomplete')
    )

    class Meta():
        model = Profile
        fields = ['twitter', 'location']

    def clean_twitter(self):
        """Stripe @ from beginning of Twitter name, if it exists."""
        twitter = self.cleaned_data['twitter']
        return twitter.split('@')[-1]


class EmailSettingsForm(forms.ModelForm):
    """A form for updating user email preferences."""

    class Meta():
        model = Profile
        fields = ['email_pref', 'use_autologin']


class OrgPreferencesForm(forms.ModelForm):
    """A form for updating user organization preferences"""

    active_org = OrganizationChoiceField(
        queryset=Organization.objects.none(),
        empty_label=None,
        label='Choose active organization',
        help_text=
        "You can also change your current organizational page by hovering over "
        "your name (or tapping it on mobile), and then selecting the "
        "organization you'd like to use from the selection that appears.",
    )

    def __init__(self, *args, **kwargs):
        super(OrgPreferencesForm, self).__init__(*args, **kwargs)
        self.fields['active_org'].queryset = (
            self.instance.user.organizations.order_by('-individual', 'name')
        )
        self.fields['active_org'].initial = self.instance.organization

    def save(self, *args, **kwargs):
        """Set the active organization in addition to saving the other preferences"""
        super(OrgPreferencesForm, self).save(*args, **kwargs)
        self.instance.organization = self.cleaned_data['active_org']

    class Meta():
        model = Profile
        fields = ['org_share']


class BuyRequestForm(StripeForm):
    """Form for buying more requests"""

    num_requests = forms.IntegerField(
        label='Number of requests to buy',
        min_value=1,
    )

    def __init__(self, *args, **kwargs):
        super(BuyRequestForm, self).__init__(*args, **kwargs)
        if self._user.is_authenticated and self._user.profile.is_advanced():
            limit_val = 1
        else:
            limit_val = 4
        self.fields['num_requests'].validators[0].limit_value = limit_val
        self.fields['num_requests'].widget.attrs['min'] = limit_val
        self.fields['num_requests'].initial = limit_val


class ContactForm(forms.Form):
    """A form for contacting the user"""

    subject = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea)
