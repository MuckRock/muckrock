"""
Tests for crowdfund app
"""

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, Client

from datetime import datetime, date, timedelta
from decimal import Decimal
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.crowdfund.forms import CrowdfundPaymentForm
from muckrock.crowdfund.models import CrowdfundPayment
from muckrock.crowdfund.views import CrowdfundDetailView, crowdfund_embed_view
from muckrock.factories import UserFactory, FOIARequestFactory, ProjectFactory, CrowdfundFactory
from muckrock.project.models import ProjectCrowdfunds
from muckrock.utils import mock_middleware


@patch('stripe.Charge', Mock(create=Mock(return_value=Mock(id='stripe-charge-id'))))
class TestCrowdfundView(TestCase):
    """Tests the Detail view for Crowdfund objects"""
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

    def post(self, data, user=AnonymousUser()):
        """Helper function to post the data as the user."""
        # need a unique token for each POST
        form = CrowdfundPaymentForm(data)
        ok_(form.is_valid(), form.errors)
        request = self.request_factory.post(self.url, data=data)
        request = mock_middleware(request)
        request.user = user
        response = self.view(request, pk=self.crowdfund.pk)
        ok_(response, 'There should be a response.')
        eq_(response.status_code, 302,
            'The response should be a redirection.')
        eq_(response.url, self.crowdfund.get_crowdfund_object().get_absolute_url(),
            'The response should redirect to the crowdfund object.')
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
        amount = Decimal(self.data['stripe_amount']/100)
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

    def test_xframe_options(self):
        """The embed view should have permissive X-Frame-Options"""
        response = self.client.get(self.url)
        eq_(response.status_code, 200)
