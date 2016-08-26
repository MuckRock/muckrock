"""
Tests for crowdfund app
"""

from django.test import TestCase

from datetime import datetime, timedelta
from decimal import Decimal
from mock import Mock
from nose.tools import ok_, assert_false

from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.models import FOIARequest

class TestCrowdfundForm(TestCase):
    """Tests the form used to create a crowdfund campaign."""

    def setUp(self):
        self.form = CrowdfundForm()
        foia = Mock(FOIARequest)
        foia.id = 1
        foia.price = Decimal(100.00)
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
        form = CrowdfundForm(initial=self.data)
        ok_(form)

    def test_empty_validation(self):
        """An empty form should not validate."""
        assert_false(self.form.is_valid())

    def test_expected_validation(self):
        """Given a correct set of data, the form should validate."""
        form = CrowdfundForm(self.data)
        ok_(form.is_valid(), 'The form should validate.')

    def test_zero_amount(self):
        """Payment required should not be zero."""
        data = self.data
        data['payment_required'] = 0
        form = CrowdfundForm(data)
        assert_false(form.is_valid(), 'The form should not validate.')

    def test_negative_amount(self):
        """Payment required should not be negative."""
        data = self.data
        data['payment_required'] = -10.00
        form = CrowdfundForm(data)
        assert_false(form.is_valid(), 'The form should not validate.')

    def test_incorrect_deadline(self):
        """The crowdfund deadline cannot be set in the past. That makes no sense!"""
        data = self.data
        yesterday = datetime.now() - timedelta(1)
        data['date_due'] = yesterday.strftime('%Y-%m-%d')
        form = CrowdfundForm(data)
        assert_false(form.is_valid(), 'The form should not validate.')

    def test_incorrect_duration(self):
        """The crowdfund duration should be capped at 30 days."""
        data = self.data
        too_long = datetime.now() + timedelta(45)
        data['date_due'] = too_long.strftime('%Y-%m-%d')
        form = CrowdfundForm(data)
        assert_false(form.is_valid(), 'The form should not validate.')
