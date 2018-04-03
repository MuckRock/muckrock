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
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.message.tasks import email_change
from muckrock.organization.models import Organization


class ProfileSettingsForm(forms.ModelForm):
    """A form for updating user information"""
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    location = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget('JurisdictionLocalAutocomplete')
    )

    class Meta():
        model = Profile
        fields = ['first_name', 'last_name', 'avatar', 'twitter', 'location']

    def clean_twitter(self):
        """Stripe @ from beginning of Twitter name, if it exists."""
        twitter = self.cleaned_data['twitter']
        return twitter.split('@')[-1]

    def save(self, commit=True):
        """Modifies associated User model."""
        profile = super(ProfileSettingsForm, self).save(commit)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        profile.user.save()
        return profile


class EmailSettingsForm(forms.ModelForm):
    """A form for updating user email preferences."""
    email = forms.EmailField()

    class Meta():
        model = Profile
        fields = ['email', 'email_pref', 'use_autologin']

    def clean_email(self):
        """Validates that a user does not exist with the given e-mail address"""
        email = self.cleaned_data['email']
        users = User.objects.filter(email__iexact=email)
        if users.count() == 1 and users.first() != self.instance.user:
            raise forms.ValidationError(
                'A user with that e-mail address already exists.'
            )
        if users.count() > 1:  # pragma: no cover
            # this should never happen
            raise forms.ValidationError(
                'A user with that e-mail address already exists.'
            )
        return email

    def save(self, commit=True):
        """Modifies associated User and Stripe.Customer models"""
        profile = super(EmailSettingsForm, self).save(commit)
        user = profile.user
        old_email = user.email
        new_email = self.cleaned_data['email']
        if old_email != new_email:
            customer = profile.customer()
            user.email = new_email
            customer.email = new_email
            profile.email_failed = False
            profile.email_confirmed = False
            profile.generate_confirmation_key()
            user.save()
            customer.save()
            profile.save()
            # notify the user
            email_change.delay(user, old_email)
        return profile


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


class RegisterForm(UserCreationForm):
    """Register for a basic account"""

    class Meta(UserCreationForm.Meta):
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password1',
            'password2'
        ]

    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(
        label='Password Confirmation', widget=forms.PasswordInput()
    )

    def clean_username(self):
        """Do a case insensitive uniqueness check and clean username input"""
        username = self.cleaned_data['username']
        username = re.sub(
            r'[^\w\-.@ ]', '', username
        )  # strips illegal characters from username
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is taken.")
        return username

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError(
                "An account with this email already exists."
            )
        return email


class RegistrationCompletionForm(SetPasswordForm):
    """Adds username to the SetPasswordForm"""
    username = forms.CharField()

    def clean_username(self):
        """Do a case insensitive uniqueness check and clean username input"""
        username = self.cleaned_data['username']
        username = re.sub(
            r'[^\w\-.@ ]', '', username
        )  # strips illegal characters from username
        existing_user = User.objects.filter(username__iexact=username)
        if existing_user.exists() and existing_user.first() != self.user:
            raise forms.ValidationError("This username is taken.")
        return username

    def save(self, commit=True):
        self.user = super(RegistrationCompletionForm, self).save(commit)
        username = self.cleaned_data['username']
        self.user.username = username
        if commit:
            self.user.save()
        return self.user


class RegisterOrganizationForm(RegisterForm):
    """Register for an organization account"""
    organization_name = forms.CharField(
        min_length=2,
        max_length=255,
    )

    def clean_organization_name(self):
        """Check for an existing organizaiton."""
        organization_name = self.cleaned_data['organization_name']
        slug = slugify(organization_name)
        try:
            Organization.objects.get(slug=slug)
        except Organization.DoesNotExist:
            return organization_name
        raise forms.ValidationError(
            'Organization already exists with this name.'
        )

    def create_organization(self, owner):
        """Creates and returns an organization from the form data"""
        return Organization.objects.create(
            name=self.cleaned_data['organization_name'], owner=owner
        )


class StripeForm(forms.Form):
    """Form for processing stripe payments"""
    stripe_token = forms.CharField(widget=forms.HiddenInput())
    stripe_pk = forms.CharField(
        widget=forms.HiddenInput(),
        initial=settings.STRIPE_PUB_KEY,
    )
    stripe_image = forms.CharField(
        widget=forms.HiddenInput(),
        initial=static('icons/logo.png'),
    )
    stripe_email = forms.CharField(widget=forms.HiddenInput())
    stripe_label = forms.CharField(widget=forms.HiddenInput(), initial='Buy')
    stripe_description = forms.CharField(widget=forms.HiddenInput())
    stripe_fee = forms.IntegerField(
        widget=forms.HiddenInput(),
        initial=0,
        min_value=0,
    )
    stripe_amount = forms.IntegerField(widget=forms.HiddenInput(), min_value=0)


class BuyRequestForm(StripeForm):
    """Form for buying more requests"""
    num_requests = forms.IntegerField(
        label='Number of requests to buy',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(BuyRequestForm, self).__init__(*args, **kwargs)
        if self.user.is_authenticated:
            self.fields['stripe_email'].initial = self.user.email
        # XXX ensure min validation works
        if self.user.is_authenticated and self.user.profile.is_advanced():
            self.fields['num_requests'].min_value = 1
            self.fields['num_requests'].widget.attrs['min'] = 1
        else:
            self.fields['num_requests'].min_value = 4
            self.fields['num_requests'].widget.attrs['min'] = 4
