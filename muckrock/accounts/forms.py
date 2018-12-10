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
