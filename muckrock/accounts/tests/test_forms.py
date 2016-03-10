"""
Tests accounts forms
"""

from django.test import TestCase

from nose.tools import eq_, assert_false, assert_true
from mock import patch

from muckrock.accounts.forms import EmailSettingsForm, RegisterForm
from muckrock.factories import UserFactory, ProfileFactory

class TestEmailSettingsForm(TestCase):
    """Users should be able to modify their email settings."""
    def setUp(self):
        """Set up tests"""
        # pylint:disable=no-member
        self.profile = ProfileFactory()
        self.data = {
            'email_pref': self.profile.email_pref,
            'use_autologin': self.profile.use_autologin,
            'email': self.profile.user.email
        }
        self.form = EmailSettingsForm

    @patch('muckrock.message.tasks.email_change.delay')
    def test_email_normal(self, mock_notify):
        """Changing email normally should succeed"""
        old_email = self.profile.user.email
        new_email = 'new@example.com'
        self.data['email'] = new_email
        form = self.form(self.data, instance=self.profile)
        assert_true(form.is_valid())
        eq_(form.clean_email(), new_email)
        form.save()
        mock_notify.assert_called_once_with(self.profile.user, old_email)

    @patch('muckrock.message.tasks.email_change.delay')
    def test_email_same(self, mock_notify):
        """Keeping email the same should succeed"""
        form = self.form(self.data, instance=self.profile)
        assert_true(form.is_valid())
        eq_(form.clean_email(), self.profile.user.email)
        form.save()
        mock_notify.assert_not_called()

    def test_email_conflict(self):
        """Trying to use an already taken email should fail"""
        other_user = UserFactory()
        self.data['email'] = other_user.email
        form = self.form(self.data, instance=self.profile)
        assert_false(form.is_valid())


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
