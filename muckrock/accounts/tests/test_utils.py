"""
Tests the accounts utility methods
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

# Standard Library
import re

# Third Party
import requests_mock
from mock.mock import Mock
from nose.tools import eq_, ok_

# MuckRock
from muckrock.accounts.mixins import MiniregMixin
from muckrock.accounts.utils import unique_username
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import mock_middleware, mock_squarelet
from muckrock.organization.factories import FreeEntitlementFactory


class TestMiniregister(TestCase):
    """Miniregistration allows a user to sign up for an account with their full name and email."""

    def setUp(self):
        self.full_name = 'Lou Reed'
        self.email = 'lou@hero.in'

    @requests_mock.Mocker()
    def test_expected_case(self, mock_requests):
        """
        Giving the miniregister method a full name, email, and password should
        create a user, create a profile, and log them in.
        The method should return the authenticated user.
        """

        mock_squarelet(mock_requests)
        FreeEntitlementFactory()

        request = RequestFactory()
        mixin = MiniregMixin()
        form = Mock()
        mixin.request = mock_middleware(request.get(reverse('foia-create')))
        user = mixin.miniregister(form, self.full_name, self.email)
        ok_(isinstance(user, User), 'A user should be created and returned.')
        ok_(user.profile, 'A profile should be created for the user.')
        ok_(user.is_authenticated(), 'The user should be logged in.')
        eq_(user.profile.full_name, 'Lou Reed')
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
        eq_(user.username, 'Highlander')
        ok_(re.match(name + r'_[a-zA-Z]{8}', unique_username(name)))
        lower_name = name.lower()
        ok_(re.match(lower_name + r'_[a-zA-Z]{8}', unique_username(lower_name)))
