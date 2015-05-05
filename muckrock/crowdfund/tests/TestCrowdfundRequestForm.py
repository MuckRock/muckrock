"""
Tests for crowdfund app
"""

from django.test import TestCase, Client

from datetime import datetime, timedelta
from decimal import Decimal
import logging
import nose
import stripe

from muckrock.crowdfund.forms import CrowdfundRequestForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.models import FOIARequest

# pylint: disable=missing-docstring

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

class TestCrowdfundRequestForm(TestCase):

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.form = CrowdfundRequestForm()
        foia = FOIARequest.objects.get(pk=18)
        due = datetime.today() + timedelta(30)
        self.data = {
            'name': 'Crowdfund this Request',
            'description': 'Let\'s "payve" the way forward!',
            'payment_required': foia.price,
            'date_due': due.strftime('%Y-%m-%d'),
            'foia': foia.id
        }

    def test_prefilled_request_form(self):
        """An empty crowdfund form should prefill with everything it needs to validate."""
        form = CrowdfundRequestForm(initial=self.data)
        ok_(form)

    def test_empty_validation(self):
        """An empty form should not validate."""
        ok_(not self.form.is_valid())

    def test_expected_validation(self):
        """Given a correct set of data, the form should validate."""
        form = CrowdfundRequestForm(self.data)
        ok_(form.is_valid())

    def test_zero_amount(self):
        data = self.data
        data['payment_required'] = 0
        form = CrowdfundRequestForm(data)
        ok_(not form.is_valid(),
            'Payment required should not be zero')

    def test_negative_amount(self):
        data = self.data
        data['payment_required'] = -10.00
        form = CrowdfundRequestForm(data)
        ok_(not form.is_valid(),
            'Payment required should not be negative')

    def test_incorrect_deadline(self):
        """The crowdfund deadline cannot be set in the past. That makes no sense!"""
        data = self.data
        yesterday = datetime.now() - timedelta(1)
        data['date_due'] = yesterday.strftime('%Y-%m-%d')
        form = CrowdfundRequestForm(data)
        ok_(not form.is_valid(),
            'The form should not validate given a date in the past.')

    def test_incorrect_duration(self):
        """The crowdfund duration should be capped at 30 days."""
        data = self.data
        too_long = datetime.now() + timedelta(45)
        data['date_due'] = too_long.strftime('%Y-%m-%d')
        form = CrowdfundRequestForm(data)
        ok_(not form.is_valid(),
            'The form should not validate, given a deadline too far in the future.')
