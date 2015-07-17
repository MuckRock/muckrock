"""
Test organization view classes and functions
"""

from django.test import TestCase

from nose.tools import ok_

class TestOrgCreate(TestCase):
    """Test the expectations of organization creation"""

    def test_staff_only(self):
        """Only MuckRock staff may create a new organization."""
        ok_(False, 'Test unwritten.')

    def test_owner_is_member(self):
        """The organization owner should be saved as a member."""
        ok_(False, 'Test unwritten.')

class TestOrgActivation(TestCase):
    """Test the expectations of organization activation"""

    def test_activation(self):
        """
        When activating the organization, a Stripe plan should be created and
        the owner should be subscribed to the plan.
        """
        ok_(False, 'Test unwritten.')

    def test_staff_or_owner_only(self):
        """Only MuckRock staff or the organization owner may activate the org."""
        ok_(False, 'Test unwritten.')

    def test_already_active(self):
        """An already-active org should not be able to be activated."""
        ok_(False, 'Test unwritten.')

class TestOrgDeactivation(TestCase):
    """Test the expectations of organization deactivation"""

    def test_deactivation(self):
        """
        When deactivating the organization, the owner should be unsubscribed from
        the org's plan but the plan should not be deleted.
        """
        ok_(False, 'Test unwritten.')

    def test_staff_or_owner_only(self):
        """Only MuckRock staff or the organization owner may deactivate the org."""
        ok_(False, 'Test unwritten.')

    def test_already_inactive(self):
        """An already-inactive org should not be able to be deactivated."""
        ok_(False, 'Test unwritten.')
