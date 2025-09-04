# -*- coding: utf-8 -*-
"""
Tests for communication
"""

# Django
from django.forms import ValidationError
from django.test import TestCase

# Third Party
import pytest

# MuckRock
from muckrock.communication.models import EmailAddress
from muckrock.foia.factories import FOIARequestFactory
from muckrock.mailgun.models import WhitelistDomain


class TestEmailAddress(TestCase):
    """Test the email address model"""

    def test_fetch(self):
        """Test the fetch query set method"""
        assert isinstance(EmailAddress.objects.fetch("test@example.com"), EmailAddress)
        assert EmailAddress.objects.fetch("foobar") is None

    def test_fetch_many(self):
        """Test the fetch_many query set method"""
        assert len(EmailAddress.objects.fetch_many("a@a.com, b@b.com, foobar")) == 2
        with pytest.raises(ValidationError):
            EmailAddress.objects.fetch_many("a@a.comn, foobar", ignore_errors=False)

    def test_allowed(self):
        """Test allowed email function"""
        foia = FOIARequestFactory(
            email__email="foo@bar.com",
            cc_emails="foo@baz.com",
            agency__email__email__email="main@agency.com",
            agency__other_emails="foo@agency.com",
        )
        WhitelistDomain.objects.create(domain="whitehat.edu")

        allowed_emails = [
            "foo@bar.com",  # primary email
            "foo@BAR.COM",  # case insensitive
            "foo@baz.com",  # other email
            "foo@agency.com",  # agency email
            "any@usa.gov",  # any government tld
            "any@domain.ma.us",  # any government tld
            "foo@whitehat.edu",  # white listed domain
        ]
        not_allowed_emails = [
            "other@baz.com",
            "other@agency.com",
            "random@random.edu",
            "foo@co.uk",
        ]
        for email in allowed_emails:
            assert EmailAddress.objects.fetch(email).allowed(foia), (
                "Allowed email failed for address %s" % email
            )
        for email in not_allowed_emails:
            assert not EmailAddress.objects.fetch(email).allowed(foia), (
                "Non allowed email failed for address %s" % email
            )
        # non foia test - any agency email
        assert EmailAddress.objects.fetch("main@agency.com").allowed()

    def test_domain(self):
        """Test the domain method"""
        assert EmailAddress.objects.fetch("a@a.com").domain == "a.com"
        assert (
            EmailAddress.objects.fetch('"odd_email@you"@weird.com').domain
            == "weird.com"
        )

    def test_str(self):
        """Test the __str__ method"""
        email = '"John Doe" <john@doe.com>'
        assert str(EmailAddress.objects.fetch(email)) == email
