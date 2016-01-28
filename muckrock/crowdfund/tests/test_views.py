"""
Tests for crowdfund app
"""

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.crowdfund.forms import CrowdfundPaymentForm
from muckrock.crowdfund.models import Crowdfund, CrowdfundPayment
from muckrock.crowdfund.views import CrowdfundDetailView
from muckrock.factories import UserFactory, FOIARequestFactory, ProjectFactory
from muckrock.utils import mock_middleware

class TestCrowdfundDetailView(TestCase):
    """Tests the helper method in the DetailView subclass"""

    def setUp(self):
        self.view = CrowdfundDetailView()
        self.view.form = CrowdfundPaymentForm()
        self.mock_url = '/mock-123/'
        self.crowdfund = Mock()
        project = Mock()
        project.get_absolute_url = Mock(return_value=self.mock_url)
        self.crowdfund.get_crowdfund_object = Mock(return_value=project)
        self.view.get_object = Mock(return_value=self.crowdfund)

    def test_get_form(self):
        """Should return a form or nothing"""
        logging.debug(self.view.get_form())
        ok_(isinstance(self.view.get_form(), CrowdfundPaymentForm))
        self.view.form = None
        ok_(self.view.get_form() is None)

    def test_get_redirect_url(self):
        """Should return a redirect url or the index url"""
        eq_(self.view.get_redirect_url(), self.mock_url,
            'The function should return the url of the crowdfund object.')
        self.crowdfund.get_crowdfund_object = Mock(return_value=None)
        self.view.get_object = Mock(return_value=self.crowdfund)
        eq_(self.view.get_redirect_url(), reverse('index'),
            ('The function should return the index url as a fallback '
            'if the url cannot be reversed.'))

@patch('stripe.Charge', Mock())
class TestCrowdfundView(TestCase):
    """Tests the Detail view for Crowdfund objects"""
    def setUp(self):
        # pylint:disable=no-member
        foia = FOIARequestFactory(status='payment', price=10.00)
        due = datetime.today() + timedelta(30)
        self.crowdfund = Crowdfund.objects.create(
            foia=foia,
            name='Test Crowdfund',
            description='Testing contributions to this request',
            payment_required=foia.price,
            date_due=due
        )
        self.num_payments = self.crowdfund.payments.count()
        self.url = self.crowdfund.get_absolute_url()
        self.data = {
            'amount': 200,
            'show': '',
            'crowdfund': self.crowdfund.pk,
            'email': 'test@example.com',
            'token': 'test'
        }
        self.view = CrowdfundDetailView.as_view()
        self.request_factory = RequestFactory()

    def test_view(self):
        """The crowdfund view should resolve and be visible to everyone."""
        request = self.request_factory.get(self.url)
        response = self.view(request, pk=self.crowdfund.pk)
        eq_(response.status_code, 200, 'The response should be 200 OK.')

    def post(self, data, user=AnonymousUser()):
        """Helper function to post the data as the user."""
        # need a unique token for each POST
        form = CrowdfundPaymentForm(data)
        ok_(form.is_valid())
        request = self.request_factory.post(self.url, data=data)
        request = mock_middleware(request)
        request.user = user
        response = self.view(request, pk=self.crowdfund.pk)
        ok_(response, 'There should be a response.')
        return response

    def test_anonymous_contribution(self):
        """
        After posting the payment, the email, and the token, the server should process the
        payment before creating and returning a payment object.
        """
        self.post(self.data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.user, None,
            ('If the user is logged out, the returned payment'
            ' object should not reference any account.'))
        eq_(self.crowdfund.payments.count(), self.num_payments + 1,
            'The crowdfund should have the payment added to it.')

    def test_anonymous_while_logged_in(self):
        """
        An attributed contribution checks if the user is logged in, but still
        defaults to anonymity.
        """
        user = UserFactory()
        self.post(self.data, user)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.user.username, user.username,
            'The logged in user should be associated with the payment.')
        eq_(payment.show, False,
            'If the user wants to be anonymous, then the show flag should be false.')
        eq_(self.crowdfund.payments.count(), self.num_payments + 1,
            'The crowdfund should have the payment added to it.')

    def test_attributed_contribution(self):
        """An attributed contribution is opted-in by the user"""
        user = UserFactory()
        self.data['show'] = True
        self.post(self.data, user)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.user.username, user.username,
            'The logged in user should be associated with the payment.')
        eq_(payment.show, True,
            'If the user wants to be attributed, then the show flag should be true.')
        eq_(self.crowdfund.payments.count(), self.num_payments + 1,
            'The crowdfund should have the payment added to it.')

    def test_correct_amount(self):
        """
        Amounts come in from stripe in units of .01. The payment object should
        account for this and transform it into a Decimal object for storage.
        """
        self.post(self.data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        amount = Decimal(self.data['amount']/100)
        eq_(payment.amount, amount)

    def test_contributors(self):
        """The crowdfund can get a list of all its contibutors by parsing its list of payments."""
        # anonymous payment
        self.post(self.data)
        # anonymous payment
        user1 = UserFactory()
        self.post(self.data, user1)
        # attributed payment
        user2 = UserFactory()
        self.data['show'] = True
        self.post(self.data, user2)

        new_crowdfund = Crowdfund.objects.get(pk=self.crowdfund.pk)
        eq_(new_crowdfund.contributors_count(), 3,
                'All contributions should return some kind of user')
        eq_(new_crowdfund.anonymous_contributors_count(), 2,
                'There should be 2 anonymous contributors')
        eq_(len(new_crowdfund.named_contributors()), 1,
                'There should be 1 named contributor')

    def test_unlimit_amount(self):
        """The amount paid should be able to exceed the amount required."""
        data = self.data
        amount_paid = 20000
        data['amount'] = amount_paid
        self.post(data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.amount, 200.00,
            'The payment should be made in full despite exceeding the amount required.')

    def test_limit_amount(self):
        """No more than the amount required should be paid if the crowdfund is capped."""
        self.crowdfund.payment_capped = True
        self.crowdfund.save()
        data = self.data
        data['amount'] = 20000
        self.post(data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.amount, self.crowdfund.payment_required,
            'The amount should be capped at the crowdfund\'s required payment.')

    def test_invalid_positive_integer(self):
        """The crowdfund should accept payments with cents."""
        self.crowdfund.payment_required = Decimal('257.05')
        self.crowdfund.payment_received = Decimal('150.00')
        self.crowdfund.save()
        cent_payment = 105 # $1.05
        self.data['amount'] = cent_payment
        self.post(self.data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.amount, Decimal('01.05'))


class TestCrowdfundProjectDetailView(TestCase):
    """Tests for the crowdfund project detail view."""

    def setUp(self):
        self.crowdfund = Crowdfund.objects.create(
            name='Cool project please help',
            date_due=date.today() + timedelta(30),
            project=ProjectFactory()
        )
        self.url = self.crowdfund.get_absolute_url()
        self.data = {
            'amount': 200,
            'show': '',
            'crowdfund': self.crowdfund.pk,
            'email': 'test@example.com'
        }
        self.request_factory = RequestFactory()
        self.view = CrowdfundDetailView.as_view()

    def test_view(self):
        """The crowdfund view should resolve and be visible to everyone."""
        request = self.request_factory.get(self.url)
        response = self.view(request, pk=self.crowdfund.pk)
        eq_(response.status_code, 200, 'The response should be 200 OK.')
