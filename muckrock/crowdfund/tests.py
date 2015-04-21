"""
Tests for crowdfund app
"""

from django.test import TestCase, Client

import logging
from nose.tools import ok_, eq_
from datetime import datetime, timedelta
import stripe

from muckrock.crowdfund.forms import CrowdfundRequestForm, CrowdfundRequestPaymentForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.models import FOIARequest
from muckrock.settings import STRIPE_SECRET_KEY

# pylint: disable=missing-docstring

class TestCrowdfundRequestView(TestCase):
    """Tests the Detail view for CrowdfundRequest objects"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        stripe.api_key = STRIPE_SECRET_KEY
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
        self.data = {
            'amount': 10.00,
            'show': False,
            'crowdfund': self.crowdfund.pk
        }
        """Form submission will only happen after Stripe Checkout verifies the purchase on the front end. Assume the presence of the Stripe token and email address."""
        self.stripe_email = 'test@example.com'
        self.stripe_token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2016,
                "cvc": '123'
        })
        ok_(self.stripe_token)

    def test_view(self):
        response = self.client.get(self.url)
        eq_(response.status_code, 200,
            'The crowdfund view should resolve and be visible to everyone')

    def test_anonymous_contribution(self):
        """After posting the payment, the email, and the token, the server should process the payment before creating and returning a payment object."""
        form = CrowdfundRequestPaymentForm(self.data)
        if form.is_valid():
            msg = '%s' % form.cleaned_data
        else:
            msg = '%s' % form.errors
        logging.info(msg)
        ok_(form.is_valid())
        response = self.client.post(self.url, {'payment': form.data, 'email': self.stripe_email, 'token': self.stripe_token})
        ok_(False, 'Should be able to make an anonymous contribution')

    def test_attributed_contribution(self):
        """An attributed contribution checks if the user is logged in, and if they are it connects the payment to their account."""
        self.client.login(username='adam', password='123')
        self.data['show'] = True
        form = CrowdfundRequestPaymentForm(self.data)
        if form.is_valid():
            msg = '%s' % form.cleaned_data
        else:
            msg = '%s' % form.errors
        logging.info(msg)
        ok_(form.is_valid())
        response = self.client.post(self.url, {'payment': form.data, 'email': self.stripe_email, 'token': self.stripe_token})
        payment = response.context['payment']
        ok_(payment)
        eq_(payment.user.username, 'adam',
            ('If the user is logged in and opts into attribution, the returned'
            ' payment object should reference their user account.'))

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
