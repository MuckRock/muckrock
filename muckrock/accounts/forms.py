"""
Forms for accounts application
"""

# Django
from django import forms
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import validate_email

# Standard Library
import logging

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core.utils import squarelet_post
from muckrock.jurisdiction.models import Jurisdiction
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
    # XXX remove
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


# XXX move to orgs


class OrganizationChoiceField(forms.ModelChoiceField):
    """Custom labels for organization choice field"""

    def label_from_instance(self, obj):
        """Change individual organization label to personal account"""
        if obj.individual:
            return 'Personal Account'
        else:
            return super(OrganizationChoiceField, self).label_from_instance(obj)


class StripeForm(forms.Form):
    """Form for processing stripe payments"""
    stripe_token = forms.CharField(widget=forms.HiddenInput(), required=False)
    stripe_pk = forms.CharField(
        widget=forms.HiddenInput(), initial=settings.STRIPE_PUB_KEY
    )
    organization = OrganizationChoiceField(
        queryset=Organization.objects.none(),
        empty_label=None,
        label='Pay from which account',
    )
    use_card_on_file = forms.TypedChoiceField(
        label='Use Credit Card on File',
        coerce=lambda x: x == 'True',
        initial=True,
        widget=forms.RadioSelect,
        choices=(
            (True, 'Card on File'),
            (False, 'New Card'),
        )
    )
    save_card = forms.BooleanField(
        label="Save credit card information",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        self._user = kwargs.pop('user')
        super(StripeForm, self).__init__(*args, **kwargs)

        # if auth user and org are given
        if self._user.is_authenticated and self._organization is not None:
            del self.fields['organization']
            if self._organization.card:
                self.fields['use_card_on_file'].choices = (
                    (True, self._organization.card),
                    (False, 'New Card'),
                )
            else:
                del self.fields['use_card_on_file']
                self.fields['stripe_token'].required = True

        # if auth user no no org are given
        elif self._user.is_authenticated and self._organization is None:
            queryset = self._user.organizations.filter(
                memberships__admin=True,
            ).order_by('-individual', 'name')
            if len(queryset) == 1:
                self.fields['organization'].widget = forms.HiddenInput()
            self.fields['organization'].queryset = queryset
            self.fields['organization'
                        ].initial = self._user.profile.individual_organization
            self.fields['use_card_on_file'].choices = (
                (True, self._user.profile.individual_organization.card),
                (False, 'New Card'),
            )

        # if anonymous user is given
        elif not self._user.is_authenticated:
            del self.fields['organization']
            del self.fields['use_card_on_file']
            del self.fields['save_card']

    def clean(self):
        """Validate using card on file and supplying new card"""
        data = super(StripeForm, self).clean()

        if data.get('use_card_on_file') and data.get('stripe_token'):
            self.add_error(
                'use_card_on_file',
                'You cannot use your card on file and enter a credit card number.',
            )

        if data.get('save_card') and not data.get('stripe_token'):
            self.add_error(
                'save_card',
                'You must enter credit card information in order to save it',
            )
        if data.get('save_card') and data.get('use_card_on_file'):
            self.add_error(
                'save_card',
                'You cannot save your card information if you are using your '
                'card on file.',
            )

        if (
            'use_card_on_file' in self.fields
            and not data.get('use_card_on_file')
            and not data.get('stripe_token')
        ):
            self.add_error(
                'use_card_on_file',
                'You must use your card on file or enter a credit card number.',
            )
        return data


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

    def get_price(self, num_requests):
        """Get the price for the requests"""
        # XXX move to mixin
        # XXX
        is_advanced = (
            self._user.is_authenticated and self._user.profile.is_advanced()
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


# XXX foia form
class RequestFeeForm(StripeForm):
    """A form to pay request fees"""
    amount = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'currency-field'
        }),
        min_value=0,
        help_text=
        'We will add a 5% fee to this amount to cover our transaction fees.',
    )

    field_order = [
        'stripe_token',
        'stripe_pk',
        'amount',
        'organization',
        'use_card_on_file',
        'save_card',
    ]
