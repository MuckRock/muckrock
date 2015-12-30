"""
Tests accounts forms
"""

from django.test import TestCase
from django.forms import ValidationError

from nose.tools import eq_, raises, assert_false

from muckrock.accounts.forms import EmailSettingsForm, RegisterForm
from muckrock.factories import UserFactory, ProfileFactory

class TestEmailSettingsForm(TestCase):
    """Users should be able to modify their email settings."""
    def setUp(self):
        """Set up tests"""
        self.profile = ProfileFactory()
        self.form = EmailSettingsForm(instance=self.profile)

    def test_email_normal(self):
        """Changing email normally should succeed"""
        new_email = 'new@example.com'
        self.form.cleaned_data = {'email': new_email}
        eq_(self.form.clean_email(), new_email)

    def test_email_same(self):
        """Keeping email the same should succeed"""
        existing_email = self.profile.user.email
        self.form.cleaned_data = {'email': existing_email}
        eq_(self.form.clean_email(), existing_email)

    @raises(ValidationError)
    def test_email_conflict(self):
        """Trying to use an already taken email should fail"""
        other_user = UserFactory()
        self.form.cleaned_data = {'email': other_user.email}
        self.form.clean_email()


class TestRegistrationForm(TestCase):
    """New users should be created using a registration form."""
    def setUp(self):
        self.user = UserFactory()
        self.form = RegisterForm

    def test_unique_username(self):
        """Username should be unique (case insensitive)"""
        existing_username = self.user.username
        data = {
            'username': existing_username,
            'email': 'different@example.com',
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = self.form(data)
        assert_false(form.is_valid())

    def test_unique_email(self):
        """Email should be unique (case insensitive)"""
        existing_email = self.user.email
        data = {
            'username': 'different',
            'email': existing_email,
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = self.form(data)
        assert_false(form.is_valid())
