"""
Tests for crowdfund app
"""

from django.test import TestCase
from django import forms

from mock import Mock
from nose.tools import ok_, eq_, raises
from datetime import datetime, timedelta

from muckrock.crowdfund.forms import CrowdfundRequestForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.models import FOIARequest

class TestCrowdfundRequestForm(TestCase):

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.form = CrowdfundRequestForm()
        foia = FOIARequest.objects.get(pk=18)
        due = datetime.now() + timedelta(30)
        self.data = {
            'name': 'Crowdfund this Request',
            'description': 'Let\'s "payve" the way forward!',
            'amount': foia.price,
            'deadline': due
        }

    def test_empty_request_form(self):
        ok_(self.form)

    def test_prefilled_request_form(self):
        form = CrowdfundRequestForm(initial=self.data)
        ok_(form)

    def test_empty_validation(self):
        ok_(not self.form.is_valid(),
            'An empty form should not validate')

    def test_expected_validation(self):
        form = CrowdfundRequestForm(self.data)
        ok_(form.is_valid())
