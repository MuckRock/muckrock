"""
Forms for accounts application
"""

# Django
from django import forms
from django.conf import settings
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import validate_email
from django.utils.text import slugify

# Standard Library
import re

# Third Party
import stripe
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core.utils import stripe_retry_on_error
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


class BillingPreferencesForm(forms.ModelForm):
    """A form for updating billing preferences."""
    stripe_token = forms.CharField()

    class Meta():
        model = Profile
        fields = ['stripe_token']

    def save(self, commit=True):
        """Modifies associated Profile and Stripe.Customer model"""
        profile = super(BillingPreferencesForm, self).save(commit)
        profile.payment_failed = False
        profile.save()
        token = self.cleaned_data['stripe_token']
        customer = profile.customer()
        customer.source = token
        customer.save()
        return profile


class OrgPreferencesForm(forms.ModelForm):
    """A form for updating user organization preferences"""

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
    stripe_token = forms.CharField(widget=forms.HiddenInput())
    stripe_pk = forms.CharField(
        widget=forms.HiddenInput(),
        initial=settings.STRIPE_PUB_KEY,
        required=False,
    )
    stripe_image = forms.CharField(
        widget=forms.HiddenInput(),
        initial=static('icons/logo.png'),
        required=False,
    )
    stripe_email = forms.EmailField(widget=forms.HiddenInput())
    stripe_label = forms.CharField(
        widget=forms.HiddenInput(),
        initial='Buy',
        required=False,
    )
    stripe_description = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )
    stripe_fee = forms.IntegerField(
        widget=forms.HiddenInput(),
        initial=0,
        required=False,
    )
    stripe_amount = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
    )


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
        stripe_retry_on_error(
            stripe.Charge.create,
            amount=self.get_price(num_requests),
            currency='usd',
            source=self.cleaned_data['stripe_token'],
            metadata={
                'email': self.cleaned_data['stripe_email'],
                'action': 'request-purchase',
                'amount': num_requests,
            },
            idempotency_key=True,
        )
        recipient.profile.add_requests(num_requests)

    def get_price(self, num_requests):
        """Get the price for the requests"""
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
