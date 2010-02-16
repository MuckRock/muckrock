"""
Forms for muckrock project
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserChangeForm(forms.Form):
    """A form for updating user information"""

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    # user is populated in the view in order for
    # clean_email to have access to the current user
    user = None

    def clean_email(self):
        """Validates that a user does not exist with the given e-mail address"""
        email = self.cleaned_data['email']
        users = User.objects.filter(email__iexact=email)
        if len(users) == 1 and users[0] != self.user:
            raise forms.ValidationError('A user with that e-mail address already exists.')
        if len(users) > 1:
            # this should never happen
            raise forms.ValidationError('A user with that e-mail address already exists.')

        return email


class MyUserCreationForm(UserCreationForm):
    """A form for creating a new user"""

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    def save(self, commit=True):
        """Save the newly created user"""

        user = UserCreationForm.save(self, commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_email(self):
        """Validates that a user does not exist with the given e-mail address """

        email = self.cleaned_data['email']
        users = User.objects.filter(email__iexact=email)
        if len(users) != 0:
            raise forms.ValidationError('A user with that e-mail address already exists.')
        return email

