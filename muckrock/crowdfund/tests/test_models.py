# -*- coding: utf-8 -*-
"""
Tests for crowdfunding models
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date, timedelta
from decimal import Decimal

# Third Party
import stripe
from mock import Mock, patch
from nose.tools import eq_, nottest, ok_, raises

# MuckRock
from muckrock.core.factories import ProjectFactory
from muckrock.core.utils import get_stripe_token
from muckrock.crowdfund import models
from muckrock.project.models import ProjectCrowdfunds
from muckrock.task.models import CrowdfundTask


def create_project_crowdfund():
    """Helper function to create a project crowdfund"""
    crowdfund = models.Crowdfund.objects.create(
        name='Cool project please help',
        payment_required=Decimal(50),
        date_due=(date.today() + timedelta(30)),
    )
    project = ProjectFactory()
    ProjectCrowdfunds.objects.create(crowdfund=crowdfund, project=project)
    return crowdfund


class TestCrowdfundAbstract(TestCase):
    """Test methods on the abstract base class"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()

    def test_close_crowdfund(self):
        """Closing a crowdfund should raise a flag and create a task."""
        crowdfund_task_count = CrowdfundTask.objects.count()
        self.crowdfund.close_crowdfund()
        self.crowdfund.refresh_from_db()
        ok_(self.crowdfund.closed, 'The closed flag should be raised.')
        eq_(
            CrowdfundTask.objects.count(), crowdfund_task_count + 1,
            'A new crowdfund task should be created.'
        )


class TestCrowdfund(TestCase):
    """Test crowdfunding"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()
        self.project = self.crowdfund.project

    def test_unicode(self):
        """The crowdfund should express itself concisely."""
        eq_('%s' % self.crowdfund, self.crowdfund.name)

    def test_unicode_characters(self):
        """The unicode method should support unicode characters"""
        self.crowdfund.name = u'Test¢s Crowdfund'
        ok_('%s' % self.crowdfund)

    def test_get_crowdfund_object(self):
        """The crowdfund should have a project being crowdfunded."""
        eq_(self.crowdfund.get_crowdfund_object(), self.project)


@patch(
    'stripe.Charge',
    Mock(create=Mock(return_value=Mock(id='stripe-charge-id')))
)
class TestCrowdfundPayment(TestCase):
    """Test making a payment to a crowdfund"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()
        self.token = Mock()

    def test_make_payment(self):
        """Should make and return a payment object"""
        amount = Decimal(100)
        payment = self.crowdfund.make_payment(
            self.token, 'test@email.com', amount
        )
        ok_(
            isinstance(payment, models.CrowdfundPayment),
            'Making a payment should create and return a payment object'
        )

    def test_unlimit_amount(self):
        """The amount paid should be able to exceed the amount required."""
        amount = Decimal(100)
        payment = self.crowdfund.make_payment(
            self.token, 'test@email.com', amount
        )
        eq_(
            payment.amount, amount,
            'The payment should be made in full despite exceeding the amount required.'
        )

    def test_limit_amount(self):
        """No more than the amount required should be paid if the crowdfund is capped."""
        self.crowdfund.payment_capped = True
        self.crowdfund.save()
        amount = Decimal(100)
        payment = self.crowdfund.make_payment(
            self.token, 'test@email.com', amount
        )
        eq_(
            payment.amount, self.crowdfund.payment_required,
            'The amount should be capped at the crowdfund\'s required payment.'
        )
        ok_(
            self.crowdfund.closed,
            'Once the cap has been reached, the crowdfund should close.'
        )


class TestStripeIntegration(TestCase):
    """Test Stripe integration and error handling"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()
        self.amount = Decimal(1)

    @nottest
    def test_make_valid_payment(self):
        """Charge should go through when card is valid"""
        token = get_stripe_token()
        self.crowdfund.make_payment(token, 'test@email.com', self.amount)

    @nottest
    @raises(stripe.CardError)
    def test_make_invalid_payment(self):
        """Charge should not go through when card is declined"""
        token = get_stripe_token('4000000000000002')
        self.crowdfund.make_payment(token, 'test@email.com', self.amount)
