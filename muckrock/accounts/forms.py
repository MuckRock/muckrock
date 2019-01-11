"""
Forms for accounts application
"""

# Django
from django import forms
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import validate_email

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core.utils import squarelet_post
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.organization.models import Organization


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

    active_org = forms.ModelChoiceField(
        queryset=Organization.objects.none(), empty_label=None
    )

    def __init__(self, *args, **kwargs):
        super(OrgPreferencesForm, self).__init__(*args, **kwargs)
        self.fields['active_org'
                    ].queryset = self.instance.user.organizations.all()
        self.fields['active_org'].initial = self.instance.organization

    def save(self, *args, **kwargs):
        """Set the active organization in addition to saving the other preferences"""
        super(OrgPreferencesForm, self).save(*args, **kwargs)
        self.instance.organization = self.cleaned_data['active_org']

    class Meta():
        model = Profile
        fields = ['org_share']


class ReceiptForm(forms.Form):
    """Form for setting receipt emails"""
    emails = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text='Additional email addresses to send receipts to.  '
        'One per line.',
    )

    def clean_emails(self):
        """Make sure each line is a valid email"""
        emails = self.cleaned_data['emails'].split('\n')
        bad_emails = []
        for email in emails:
            try:
                validate_email(email.strip())
            except forms.ValidationError:
                bad_emails.append(email)
        if bad_emails:
            raise forms.ValidationError(
                'Invalid email: %s' % ', '.join(bad_emails)
            )
        return self.cleaned_data['emails']


class StripeForm(forms.Form):
    """Form for processing stripe payments"""
    stripe_token = forms.CharField(widget=forms.HiddenInput(), required=False)
    use_card_on_file = forms.TypedChoiceField(
        label='Use Credit Card on File',
        coerce=lambda x: x == 'True',
        initial=True,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('instance', None)
        super(StripeForm, self).__init__(*args, **kwargs)
        self._set_card_options()

    def _set_card_options(self):
        """Initialize card options"""
        card = self.organization and self.organization.card
        if card:
            self.fields['use_card_on_file'].choices = (
                (True, self.organization.card),
                (False, 'New Card'),
            )
        else:
            del self.fields['use_card_on_file']
            self.fields['stripe_token'].required = True

    def clean(self):
        """Validate using card on file and supplying new card"""
        data = super(StripeForm, self).clean()
        if data.get('use_card_on_file') and data.get('stripe_token'):
            self.add_error(
                'use_card_on_file',
                'You cannot use your card on file and enter a credit card number.',
            )
        return data


class BuyRequestForm(StripeForm):
    """Form for buying more requests"""

    num_requests = forms.IntegerField(
        label='Number of requests to buy',
        min_value=1,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(BuyRequestForm, self).__init__(*args, **kwargs)
        if self.user.is_authenticated:
            self.fields['stripe_email'].initial = self.user.email
        if self.user.is_authenticated and self.user.profile.is_advanced():
            limit_val = 1
        else:
            limit_val = 4
        self.fields['num_requests'].validators[0].limit_value = limit_val
        self.fields['num_requests'].widget.attrs['min'] = limit_val
        self.fields['num_requests'].initial = limit_val

    def buy_requests(self, recipient):
        """Buy the requests"""
        num_requests = self.cleaned_data['num_requests']
        squarelet_post(
            '/api/charges/',
            data={
                'amount': self.get_price(num_requests),
                'organization': recipient.profile.organization,
                'description': 'Purchase {} requests'.format(num_requests),
                'token': self.cleaned_data['stripe_token'],
            }
        )
        recipient.profile.add_requests(num_requests)

    def get_price(self, num_requests):
        """Get the price for the requests"""
        # XXX
        is_advanced = (
            self.user.is_authenticated and self.user.profile.is_advanced()
        )
        if num_requests >= 20 and is_advanced:
            # advanced users pay $3 for bulk purchases
            return 300 * num_requests
        elif num_requests >= 20:
            # other users pay $4 for bulk purchases
            return 400 * num_requests
        else:
            # all users pay $5 for non-bulk purchases
            return 500 * num_requests
