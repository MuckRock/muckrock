"""
Forms for accounts application
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
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

    def clean(self):
        """CC info is required"""
        token = self.cleaned_data.get('token')
        last4 = self.cleaned_data.get('last4')
        card_type = self.cleaned_data.get('card_type')

        if not token or not last4 or not card_type:
            raise forms.ValidationError('Please enter valid credit card information')

        return self.cleaned_data

    class Meta:
        # pylint: disable-msg=R0903
        model = StripeCC
        exclude = ['user']


class UpgradeSubscForm(CreditCardForm):
    """A form for subscribing to pro accounts"""

    use_on_file = forms.BooleanField(required=False, label='Use card on file', initial=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UpgradeSubscForm, self).__init__(*args, **kwargs)

        card = self.request.user.get_profile().get_cc()
        if not card:
            del self.fields['use_on_file']
        else:
            self.fields['use_on_file'].help_text = '%s ending in %s' % (card.card_type, card.last4)

    def clean(self):
        """Validate the form"""

        use_on_file = self.cleaned_data.get('use_on_file')
        token = self.cleaned_data.get('token')
        last4 = self.cleaned_data.get('last4')
        card_type = self.cleaned_data.get('card_type')

        if not use_on_file and (not token or not last4 or not card_type):
            raise forms.ValidationError('Please enter valid credit card information')

        if use_on_file and not self.request.user.get_profile().get_cc():
            raise forms.ValidationError('You do not have a credit card on file')

        return self.cleaned_data

    class Meta(CreditCardForm.Meta):
        # pylint: disable-msg=R0903
        fields = ['use_on_file', 'card_number', 'cvc', 'expiration',
                  'token', 'last4', 'card_type']


class BuyRequestForm(UpgradeSubscForm):
    """A form for buying requests"""

    save_cc = forms.BooleanField(required=False, label='Save for future use')

    def clean(self):
        """Validate the form"""

        super(BuyRequestForm, self).clean()

        save_cc = self.cleaned_data.get('save_cc')
        use_on_file = self.cleaned_data.get('use_on_file')

        if use_on_file and save_cc:
            raise forms.ValidationError('You may not use the card on file and save a new one')

        return self.cleaned_data

    class Meta(UpgradeSubscForm.Meta):
        # pylint: disable-msg=R0903
        fields = ['use_on_file', 'card_number', 'cvc', 'expiration',
                  'save_cc', 'token', 'last4', 'card_type']


class CancelSubscForm(forms.Form):
    """Cancel subscription form"""
    confirm = forms.BooleanField(label='Are you sure you want to cancel your Pro Subscription?')


class RegisterFree(UserCreationForm):
    """Register for a community account"""

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'required'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'required'}))
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'class': 'required'}))
    password2 = forms.CharField(label='Password Confirmation',
                                widget=forms.PasswordInput(attrs={'class': 'required'}))

    class Meta(UserCreationForm.Meta):
        # pylint: disable-msg=R0903
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_username(self):
        """Do a case insensitive uniqueness check"""
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("User with this Username already exists.")
        return username


class RegisterPro(RegisterFree, CreditCardForm):
    """Register for a pro account"""
    # pylint: disable-msg=R0901

    class Meta(RegisterFree.Meta):
        # pylint: disable-msg=R0903
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                  'card_number', 'cvc', 'expiration', 'token', 'last4', 'card_type']

