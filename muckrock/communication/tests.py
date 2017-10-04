# -*- coding: utf-8 -*-
"""
Tests for communication
"""

from django.test import TestCase

from nose.tools import ok_, assert_false

from muckrock.communication.models import EmailAddress
from muckrock.factories import FOIARequestFactory
from muckrock.mailgun.models import WhitelistDomain

# pylint: disable=no-self-use

class TestEmailAddress(TestCase):
    """Test the email address model"""

    def test_allowed(self):
        """Test allowed email function"""
        foia = FOIARequestFactory(
                email__email='foo@bar.com',
                cc_emails='foo@baz.com',
                agency__email__email__email='main@agency.com',
                agency__other_emails='foo@agency.com',
                )
        WhitelistDomain.objects.create(domain='whitehat.edu')

        allowed_emails = [
                'bar@bar.com', # same domain
                'BAR@BAR.COM', # case insensitive
                'foo@baz.com', # other email
                'foo@agency.com', # agency email
                'any@usa.gov', # any government tld
                'any@domain.ma.us', # any government tld
                'foo@whitehat.edu', # white listed domain
                ]
        not_allowed_emails = [
                'other@baz.com',
                'other@agency.com',
                'random@random.edu',
                'foo@co.uk',
                ]
        for email in allowed_emails:
            ok_(
                    EmailAddress.objects.fetch(email).allowed(foia),
                    'Allowed email failed for address %s' % email,
                    )
        for email in not_allowed_emails:
            assert_false(
                    EmailAddress.objects.fetch(email).allowed(foia),
                    'Non allowed email failed for address %s' % email,
                    )
        # non foia test - any agency email
        ok_(EmailAddress.objects.fetch('main@agency.com').allowed())
