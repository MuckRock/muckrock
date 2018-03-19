"""
Tests the accounts utility methods
"""

# Django
from django.contrib.auth.models import User
from django.test import TestCase

# Third Party
from mock import patch
from nose.tools import eq_, ok_

# MuckRock
from muckrock.accounts.mixins import MiniregMixin, split_name
from muckrock.accounts.utils import unique_username
from muckrock.factories import UserFactory


class TestMiniregister(TestCase):
    """Miniregistration allows a user to sign up for an account with their full name and email."""

    def setUp(self):
        self.full_name = 'Lou Reed'
        self.email = 'lou@hero.in'

    @patch('muckrock.message.tasks.welcome_miniregister.delay')
    def _test_expected_case(self, mock_welcome):
        # XXX
        """
        Giving the miniregister method a full name, email, and password should
        create a user, create a profile, send them a welcome email, and log them in.
        The method should return the authenticated user.
        """
        user, _ = miniregister(self.full_name, self.email)
        ok_(isinstance(user, User), 'A user should be created and returned.')
        ok_(user.profile, 'A profile should be created for the user.')
        ok_(user.is_authenticated(), 'The user should be logged in.')
        mock_welcome.assert_called_once()  # The user should get a welcome email
        eq_(
            user.first_name, 'Lou',
            'The first name should be extracted from the full name.'
        )
        eq_(
            user.last_name, 'Reed',
            'The last name should be extracted from the full name.'
        )
        eq_(
            user.username, 'LouReed',
            'The username should remove the spaces from the full name.'
        )


class TestUniqueUsername(TestCase):
    """The unique_username method should use a name to generate a unique username."""

    def test_clean_username(self):
        """The username should sanitize the input name."""
        eq_(
            unique_username('Allan Lasser'), 'AllanLasser',
            'Spaces should be removed.'
        )
        eq_(
            unique_username('allan@muckrock.com'), 'allan@muckrock.com',
            'Emails should be valid usernames.'
        )
        eq_(
            unique_username('???dark$$$money!!!'), 'darkmoney',
            'Illegal symbols should be removed.'
        )
        eq_(
            unique_username('?security=vulnerability'), 'securityvulnerability',
            'Names that are URL keyword arguments are DEFINITELY not allowed.'
        )

    def test_existing_username(self):
        """
        If the expected username is already registered,
        the username should get a cool number appended to it.
        If multiple sequential usernames exist, the number will
        be incremented until a username is available.
        """
        name = 'Highlander'  # there can only be one!
        username = unique_username(name)
        user = UserFactory(username=username)
        eq_(
            user.username, 'Highlander',
            'If no previous user, the name should be valid.'
        )
        eq_(
            unique_username(name), 'Highlander1',
            'If previous user, the name should have a number appended.'
        )
        eq_(
            unique_username('highlander'), 'highlander1',
            'Capitals should be ignored when determining uniqueness.'
        )


class TestSplitName(TestCase):
    """The split_name method should split a full name into a first and last name."""

    def test_single_space_name(self):
        """If the full name has two names in it, the method should return a first and last name."""
        name = 'Johnny Appleseed'
        first_name, last_name = split_name(name)
        eq_(first_name, 'Johnny')
        eq_(last_name, 'Appleseed')

    def test_multi_space_name(self):
        """
        If the full name has more than two separate names in it,
        the first name should include everything except the final name.
        """
        long_name = 'John Jacob Jingleheimer Schmidt'  # his name is my name too
        first_name, last_name = split_name(long_name)
        eq_(first_name, 'John Jacob Jingleheimer')
        eq_(last_name, 'Schmidt')

    def test_single_name(self):
        """If a single name is provided as the full name, then there should be no last name."""
        short_name = 'Zeus'
        first_name, last_name = split_name(short_name)
        eq_(first_name, 'Zeus')
        ok_(not last_name)
