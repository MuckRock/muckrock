"""
Forms for accounts application
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm as UCF
from django.contrib.auth.models import User
from django.contrib.localflavor.us.forms import USZipCodeField

from accounts.models import Profile, StripeCC
from fields import CCExpField

class ProfileForm(forms.ModelForm):
    """A form for a user profile"""
    zip_code = USZipCodeField(required=False)

    class Meta:
        # pylint: disable-msg=R0903
        model = Profile


class UserChangeForm(ProfileForm):
    """A form for updating user information"""

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta(ProfileForm.Meta):
        # pylint: disable-msg=R0903
        fields = ['first_name', 'last_name', 'email',
                  'address1', 'address2', 'city', 'state', 'zip_code', 'phone']

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


class CreditCardForm(forms.ModelForm):
    """A form for the user's CC"""

    card_number = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(
                                      attrs={'autocomplete': 'off',
                                             'class': 'card-number stripe-sensitive required'}))
    cvc = forms.CharField(max_length=4, required=False, label='CVC',
                          widget=forms.TextInput(
                              attrs={'autocomplete': 'off',
                                     'class': 'card-cvc stripe-sensitive required'}))
    expiration = CCExpField(required=False)
    token = forms.CharField(required=False, widget=forms.HiddenInput())
    last4 = forms.CharField(required=False, widget=forms.HiddenInput())
    card_type = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = StripeCC

    def clean(self):
        """CC info is only required if type is pro"""
        acct_type = self.cleaned_data.get('acct_type')
        token = self.cleaned_data.get('token')
        last4 = self.cleaned_data.get('last4')
        card_type = self.cleaned_data.get('card_type')

        if acct_type == 'pro' and (not token or not last4 or not card_type):
            raise forms.ValidationError('Please enter valid credit card information')

        return self.cleaned_data


class UserCreationForm(UCF, CreditCardForm):
    """Custimized UserCreationForm"""

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'required'}))
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'class': 'required'}))
    password2 = forms.CharField(label='Password Confirmation',
                                widget=forms.PasswordInput(attrs={'class': 'required'}))
    acct_type = forms.ChoiceField(label='Account Type',
                                  choices=(('community', 'Community'), ('pro', 'Professional')),
                                  initial='community',
                                  widget=forms.RadioSelect(attrs={'class': 'required'}))

    class Meta(UCF.Meta):
        fields = ['username', 'email', 'password1', 'password2', 'acct_type',
                  'card_number', 'cvc', 'expiration', 'token', 'last4', 'card_type']

    def clean_username(self):
        """Do a case insensitive uniqueness check"""
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("User with this Username already exists.")
        return username
