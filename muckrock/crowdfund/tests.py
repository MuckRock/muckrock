"""
Tests for crowdfund app
"""

from django.test import TestCase, Client

from datetime import datetime, timedelta
from decimal import Decimal
import logging
from nose.tools import ok_, eq_
import stripe

from muckrock.crowdfund.forms import CrowdfundRequestForm, CrowdfundRequestPaymentForm
from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundRequestPayment
from muckrock.foia.models import FOIARequest
from muckrock.settings import STRIPE_SECRET_KEY

# pylint: disable=missing-docstring
# pylint: disable=line-too-long

def get_stripe_token():
    token = stripe.Token.create(
        card={
            "number": '4242424242424242',
            "exp_month": 12,
            "exp_year": 2016,
            "cvc": '123'
    })
    ok_(token)
    return token.id

class TestCrowdfundRequestView(TestCase):
    """Tests the Detail view for CrowdfundRequest objects"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        """Form submission will only happen after Stripe Checkout verifies the purchase on the front end. Assume the presence of the Stripe token and email address."""
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
            'amount': 1000,
            'show': '',
            'crowdfund': self.crowdfund.pk,
            'email': 'test@example.com'
        }

    def test_view(self):
        response = self.client.get(self.url)
        eq_(response.status_code, 200,
            'The crowdfund view should resolve and be visible to everyone')

    def post_data(self):
        # need a unique token for each POST
        form = CrowdfundRequestPaymentForm(self.data)
        ok_(form.is_valid())
        self.data['token'] = get_stripe_token()
        logging.info(self.data)
        response = self.client.post(self.url, data=self.data)
        ok_(response, 'The server should respond to the post request')
        return response

    def test_anonymous_contribution(self):
        """After posting the payment, the email, and the token, the server should process the payment before creating and returning a payment object."""
        self.post_data()
        payment = CrowdfundRequestPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.user, None,
            ('If the user is logged out, the returned payment'
            ' object should not reference any account.'))

    def test_anonymous_while_logged_in(self):
        """An attributed contribution checks if the user is logged in, but still defaults to anonymity."""
        self.client.login(username='adam', password='abc')
        self.post_data()
        payment = CrowdfundRequestPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.user, None,
            ('If the user is logged in, the returned payment'
            ' object should not reference their account.'))

    def test_attributed_contribution(self):
        """An attributed contribution is opted-in by the user"""
        self.client.login(username='adam', password='abc')
        self.data['show'] = True
        self.post_data()
        payment = CrowdfundRequestPayment.objects.get(crowdfund=self.crowdfund)
        ok_(payment.user,
            ('If the user is logged in and opts into attribution, the returned'
            ' payment object should reference their user account.'))
        eq_(payment.user.username, 'adam',
            'The logged in user should be associated with the payment.')

    def test_correct_amount(self):
        """Amounts come in from stripe in units of .01. The payment object should account for this and transform it into a Decimal object for storage."""
        self.post_data()
        payment = CrowdfundRequestPayment.objects.get(crowdfund=self.crowdfund)
        amount = Decimal(float(self.data['amount'])/100)
        eq_(payment.amount, amount,
            'Payment object should clean and transform the amount')

    def test_contributors(self):
        """The crowdfund can get a list of all its contibutors by parsing its list of payments."""
        # anonymous payment
        self.post_data()
        # anonymous payment
        self.client.login(username='adam', password='abc')
        self.post_data()
        # attributed payment
        self.data['show'] = True
        self.post_data()

        new_crowdfund = CrowdfundRequest.objects.get(pk=self.crowdfund.pk)
        contributors = new_crowdfund.contributors()
        logging.info(contributors)
        ok_(contributors, 'Crowdfund should generate a list of contributors')
        eq_(len(contributors), 3, 'All contributions should return some kind of user')
        eq_(sum(contributor.is_anonymous() is True for contributor in contributors), 2,
            'There should only be two anonymous users in this list')

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
