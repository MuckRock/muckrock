"""
Forms for accounts application
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify

import autocomplete_light
import re

from muckrock.accounts.models import Profile
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.organization.models import Organization


class ProfileSettingsForm(forms.ModelForm):
    """A form for updating user information"""
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    location = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget('JurisdictionLocalAutocomplete'))

    class Meta():
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'twitter', 'location']

    def clean_email(self):
        """Validates that a user does not exist with the given e-mail address"""
        email = self.cleaned_data['email']
        users = User.objects.filter(email__iexact=email)
        if len(users) == 1 and users[0] != self.instance.user:
            raise forms.ValidationError('A user with that e-mail address already exists.')
        if len(users) > 1: # pragma: no cover
            # this should never happen
            raise forms.ValidationError('A user with that e-mail address already exists.')
        return email

    def clean_twitter(self):
        """Stripe @ from beginning of Twitter name, if it exists."""
        twitter = self.cleaned_data['twitter']
        return twitter.split('@')[-1]

    def save(self, commit=True):
        """Modifies asscoiated User and Stripe.Customer models."""
        profile = super(ProfileSettingsForm, self).save(commit)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        profile.user.email = self.cleaned_data['email']
        profile.user.save()
        customer = profile.customer()
        customer.email = profile.user.email
        customer.save()
        return profile


class RegisterForm(UserCreationForm):
    """Register for a basic account"""
    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Password Confirmation', widget=forms.PasswordInput())

    def clean_username(self):
        """Do a case insensitive uniqueness check and clean username input"""
        username = self.cleaned_data['username']
        username = re.sub(r'[^\w\-.@ ]', '', username) # strips illegal characters from username
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("This username is taken.")
        return username

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError("An account with this email already exists.")
        return email


class RegisterOrganizationForm(RegisterForm):
    """Register for an organization account"""
    organization_name = forms.CharField()

    def clean_organization_name(self):
        """Check for an existing organizaiton."""
        organization_name = self.cleaned_data['organization_name']
        slug = slugify(organization_name)
        try:
            Organization.objects.get(slug=slug)
        except Organization.DoesNotExist:
            return organization_name
        raise forms.ValidationError('Organization already exists with this name.')

    def create_organization(self, owner):
        """Creates and returns an organization from the form data"""
        return Organization.objects.create(name=self.cleaned_data['organization_name'], owner=owner)
