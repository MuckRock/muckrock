"""
Forms for accounts application
"""

from django import forms
from django.contrib.auth.models import User
from accounts.models import Profile

from string import digits

class ProfileForm(forms.ModelForm):
    """A form for a user profile"""

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        # increase phone max length because we will strip out extra chars
        self.fields['phone'].widget.attrs['maxlength'] = '20'

    class Meta:
        # pylint: disable-msg=R0903
        model = Profile

    def clean_zip_code(self):
        """Validate the user entered zip code"""
        zip_code = self.cleaned_data['zip_code']
        if len(zip_code) != 5 or any(d not in digits for d in zip_code):
            raise forms.ValidationError('Zip code must be 5 digits')
        return zip_code

    def clean_phone(self):
        """Validate the user entered phone number"""
        phone = self.cleaned_data['phone']
        remove = dict((ord(c), None) for c in ['(', ')', ' ', '-', '.'])
        phone = phone.translate(remove)
        if phone[0] == '1':
            phone = phone[1:]
        if len(phone) != 10 or any(d not in digits for d in phone):
            raise forms.ValidationError('Phone number must be 10 digits')
        return phone


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
