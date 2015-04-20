"""
Tests for crowdfund app
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from mock import Mock
from nose.tools import ok_, eq_, raises
from datetime import datetime, timedelta

from muckrock.crowdfund.forms import CrowdfundRequestForm, CrowdfundRequestPaymentForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.models import FOIARequest

class TestCrowdfundRequestView(TestCase):

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        foia = FOIARequest.objects.get(pk=18)
        due = datetime.today() + timedelta(30)
        self.crowdfund = CrowdfundRequest.objects.create(
            foia=foia,
            name='Test Crowdfund',
            description='Testing contributions to this request',
            payment_required=foia.price,
            date_due=due
        )
        self.url = self.crowdfund.get_absolute_url()
        self.client = Client()

    def test_view(self):
        response = self.client.get(self.url)
        eq_(response.status_code, 200,
            'The crowdfund view should resolve and be visible to everyone')

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

    def test_empty_request_form(self):
        ok_(self.form)

    def test_prefilled_request_form(self):
        form = CrowdfundRequestForm(initial=self.data)
        ok_(form)

    def test_empty_validation(self):
        ok_(not self.form.is_valid(),
            'An empty form should not validate')

    def test_expected_validation(self):
        print self.data['date_due']
        form = CrowdfundRequestForm(self.data)
        ok_(form.is_valid(),
            'Given a correct set of data, the form should validate')

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
        data = self.data
        yesterday = datetime.now() - timedelta(1)
        data['date_due'] = yesterday.strftime('%Y-%m-%d')
        form = CrowdfundRequestForm(data)
        ok_(not form.is_valid(),
            'The due date for the crowdfund must come after today')


