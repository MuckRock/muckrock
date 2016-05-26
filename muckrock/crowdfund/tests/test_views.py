"""
Tests for crowdfund app
"""

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, Client

from datetime import datetime, timedelta
from decimal import Decimal
import json
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.crowdfund.forms import CrowdfundPaymentForm
from muckrock.crowdfund.models import CrowdfundPayment
from muckrock.crowdfund.views import CrowdfundDetailView
from muckrock.factories import UserFactory, FOIARequestFactory, ProjectFactory, CrowdfundFactory
from muckrock.project.models import ProjectCrowdfunds
from muckrock.utils import mock_middleware


@patch('stripe.Charge', Mock(create=Mock(return_value=Mock(id='stripe-charge-id'))))
class TestCrowdfundView(TestCase):
    """
    The Crowdfund Detail View should be handle all the contributons made to the crowdfund.

    Contributions can be made:
    - anonymously while logged out
    - anonymously while logged in
    - onymously while logged in

    If a logged out user wants to make an onymous contribution, they need to register an account.
    We provide them with a method for registering for an account at the time of contribution.

    Crowdfund contributions should normally be made with Javascript via AJAX, and the crowdfund
    view should handle and respond with JSON when an AJAX request is made. The response to a
    successful contribution should include the user's current logged-in state and whether they
    were registered as a user at the time the contribution was made.
    """
    def setUp(self):
        due = datetime.today() + timedelta(30)
        self.crowdfund = CrowdfundFactory(date_due=due)
        FOIARequestFactory(
            status='payment',
            price=self.crowdfund.payment_required,
            crowdfund=self.crowdfund
        )
        self.num_payments = self.crowdfund.payments.count()
        self.url = self.crowdfund.get_absolute_url()
        self.data = {
            'stripe_amount': 200,
            'show': '',
            'crowdfund': self.crowdfund.pk,
            'stripe_email': 'test@example.com',
            'stripe_token': 'test'
        }
        self.view = CrowdfundDetailView.as_view()
        self.request_factory = RequestFactory()

    def test_view(self):
        """The crowdfund view should resolve and be visible to everyone."""
        request = self.request_factory.get(self.url)
        response = self.view(request, pk=self.crowdfund.pk)
        eq_(response.status_code, 200, 'The response should be 200 OK.')

    def post(self, data, user=AnonymousUser(), ajax=False):
        """Helper function to post the data as the user."""
        # need a unique token for each POST
        form = CrowdfundPaymentForm(data)
        ok_(form.is_valid(), form.errors)
        if ajax:
            request = self.request_factory.post(self.url, data=data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        else:
            request = self.request_factory.post(self.url, data=data)
        request = mock_middleware(request)
        request.user = user
        response = self.view(request, pk=self.crowdfund.pk)
        ok_(response, 'There should be a response.')
        if ajax:
            eq_(response.status_code, 200,
                'If the request was AJAX then the response should return 200 OK.')
            eq_(response['Content-Type'], 'application/json',
                'If the request was AJAX then the response should be JSON encoded.')
        else:
            eq_(response.status_code, 302, 'The response should be a redirection.')
            eq_(response.url, self.crowdfund.get_crowdfund_object().get_absolute_url(),
                'The response should redirect to the crowdfund object.')
        return response

    def test_anonymous_logged_out_contribution(self):
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

    def test_anonymous_logged_in_contribution(self):
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

    def test_onymous_logged_in_contribution(self):
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

    def test_ajax(self):
        """A contribution made via AJAX should respond with JSON."""
        self.post(self.data, ajax=True)

    def test_logged_out_ajax(self):
        """
        A contribution made via AJAX while logged out should report that:
        - the user is not authenticated
        - the user was not registered
        """
        response = self.post(self.data, ajax=True)
        data = json.loads(response.content)
        eq_(data['authenticated'], False)
        eq_(data['registered'], False)

    def test_logged_in_ajax(self):
        """
        A contribution made via AJAX while logged in should report that:
        - the user is authenticated
        - the user was not registered
        """
        response = self.post(self.data, user=UserFactory(), ajax=True)
        data = json.loads(response.content)
        eq_(data['authenticated'], True)
        eq_(data['registered'], False)

    def test_registered_ajax(self):
        """
        A contribution made via AJAX while logged out, but registering, should report that:
        - the user is authenticated
        - the user was registered
        """
        response = self.post(self.data, ajax=True)
        data = json.loads(response.content)
        eq_(data['authenticated'], True)
        eq_(data['registered'], True)

    def test_correct_amount(self):
        """
        Amounts come in from stripe in units of .01. The payment object should
        account for this and transform it into a Decimal object for storage.
        """
        self.post(self.data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        amount = Decimal(self.data['stripe_amount']/100)
        eq_(payment.amount, amount)

    def test_contributors(self):
        """The crowdfund can get a list of all its contibutors by parsing its list of payments."""
        # TODO refactor into a model test, this doesn't really deal with view logic at all.
        # anonymous logged out payment
        self.post(self.data)
        # anonymous logged in payment
        user1 = UserFactory()
        self.post(self.data, user1)
        # onymous logged in payment
        user2 = UserFactory()
        self.data['show'] = True
        self.post(self.data, user2)
        # Check to see that we're counting contributors in the right way
        self.crowdfund.refresh_from_db()
        eq_(self.crowdfund.contributors_count(), 3,
                'All contributions should return some kind of user')
        eq_(self.crowdfund.anonymous_contributors_count(), 2,
                'There should be 2 anonymous contributors')
        eq_(len(self.crowdfund.named_contributors()), 1,
                'There should be 1 named contributor')

    def test_unlimit_amount(self):
        """The amount paid should be able to exceed the amount required."""
        data = self.data
        amount_paid = 20000
        data['stripe_amount'] = amount_paid
        self.post(data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.amount, 200.00,
            'The payment should be made in full despite exceeding the amount required.')

    def test_limit_amount(self):
        """No more than the amount required should be paid if the crowdfund is capped."""
        self.crowdfund.payment_capped = True
        self.crowdfund.save()
        data = self.data
        data['stripe_amount'] = 20000
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
        self.data['stripe_amount'] = cent_payment
        self.post(self.data)
        payment = CrowdfundPayment.objects.get(crowdfund=self.crowdfund)
        eq_(payment.amount, Decimal('01.05'))


class TestCrowdfundProjectDetailView(TestCase):
    """Tests for the crowdfund project detail view."""
    def setUp(self):
        self.crowdfund = CrowdfundFactory()
        project = ProjectFactory()
        ProjectCrowdfunds.objects.create(crowdfund=self.crowdfund, project=project)
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


class TestCrowdfundEmbedView(TestCase):
    """Tests the crowdfund embed view."""
    def setUp(self):
        self.crowdfund = CrowdfundFactory()
        FOIARequestFactory(crowdfund=self.crowdfund)
        self.url = reverse('crowdfund-embed', kwargs={'pk': self.crowdfund.pk})
        self.client = Client()

    def test_get(self):
        """The embed view should render just a crowdfund widget on a standalone page."""
        response = self.client.get(self.url)
        eq_(response.status_code, 200)
