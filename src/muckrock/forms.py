
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserChangeForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    def clean_email(self):
        """
        Validates that a user does not exist with the given e-mail address.
        """
        email = self.cleaned_data['email']
        self.users_cache = User.objects.filter(email__iexact=email)
        if len(self.users_cache) == 1 and self.users_cache[0] != self.user:
            raise forms.ValidationError('A user with that e-mail address already exists.')
        if len(self.users_cache) > 1:
            # this should never happen
            raise forms.ValidationError('A user with that e-mail address already exists.')

        return email


class MyUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    def save(self, commit=True):
        user = UserCreationForm.save(self, commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_email(self):
        """
        Validates that a user does not exist with the given e-mail address.
        """
        email = self.cleaned_data['email']
        self.users_cache = User.objects.filter(email__iexact=email)
        if len(self.users_cache) != 0:
            raise forms.ValidationError('A user with that e-mail address already exists.')
        return email

