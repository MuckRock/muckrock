"""
Forms for accounts application
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.localflavor.us.forms import USZipCodeField

from accounts.models import Profile
from fields import CCExpField

class ProfileForm(forms.ModelForm):
    """A form for a user profile"""
    zip_code = USZipCodeField(required=False)

    class Meta:
        # pylint: disable=R0903
        model = Profile


class UserChangeForm(ProfileForm):
    """A form for updating user information"""

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta(ProfileForm.Meta):
        # pylint: disable=R0903
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

    name = forms.CharField(required=False, widget=forms.TextInput(
                            attrs={'class': 'card-name stripe-sensitive required'}))
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

    def clean(self):
        """CC info is required"""
        token = self.cleaned_data.get('token')

        if not token:
            raise forms.ValidationError('Please enter valid credit card information')

        return self.cleaned_data

    class Meta:
        # pylint: disable=R0903
        # This is a model form just for inheritance purposes
        model = User
        fields = ['name', 'card_number', 'cvc', 'expiration', 'token']


class PaymentForm(CreditCardForm):
    """A form for subscribing to pro accounts or buying requests"""

    use_on_file = forms.BooleanField(required=False, label='Use card on file', initial=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PaymentForm, self).__init__(*args, **kwargs)

        card = self.request.user.get_profile().get_cc()
        if not card:
            del self.fields['use_on_file']
        else:
            self.fields['use_on_file'].help_text = '%s ending in %s' % (card.type, card.last4)

    def clean(self):
        """Validate the form"""

        use_on_file = self.cleaned_data.get('use_on_file')
        token = self.cleaned_data.get('token')

        if not use_on_file and not token:
            raise forms.ValidationError('Please enter valid credit card information')

        return self.cleaned_data

    class Meta(CreditCardForm.Meta):
        # pylint: disable=R0903
        fields = ['use_on_file', 'name', 'card_number', 'cvc', 'expiration', 'token']


class CancelSubscForm(forms.Form):
    """Cancel subscription form"""
    confirm = forms.BooleanField(label='Are you sure you want to cancel your Pro Subscription?')

    def __init__(self, *args, **kwargs):
        kwargs.pop('request', None)
        super(CancelSubscForm, self).__init__(*args, **kwargs)


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
        # pylint: disable=R0903
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_username(self):
        """Do a case insensitive uniqueness check"""
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("User with this Username already exists.")
        return username

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError("User with this Email already exists.")
        return email


class RegisterPro(RegisterFree, CreditCardForm):
    """Register for a pro account"""
    # pylint: disable=R0901

    class Meta(RegisterFree.Meta):
        # pylint: disable=R0903
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                  'card_number', 'cvc', 'expiration', 'token']

