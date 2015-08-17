# -*- coding: utf-8 -*-
"""
Tests for crowdfunding models
"""

from django.test import TestCase

from datetime import date, timedelta
from decimal import Decimal
from nose.tools import eq_, ok_

from muckrock.crowdfund import models
from muckrock.foia.models import FOIARequest
from muckrock.project.models import Project

def create_project_crowdfund():
    """Helper function to create a project crowdfund"""
    crowdfund = models.CrowdfundProject.objects.create(
        name='Cool project please help',
        date_due=(date.today() + timedelta(30)),
        project=Project.objects.create(title='Test Project')
    )
    crowdfund.save()
    return crowdfund

class TestCrowdfundRequest(TestCase):
    """Test crowdfund a request"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.crowdfund = models.CrowdfundRequest()
        self.foia = FOIARequest.objects.get(pk=1)
        self.crowdfund.foia = self.foia

    def test_unicode(self):
        """The crowdfund should express itself concisely."""
        eq_('%s' % self.crowdfund, 'Crowdfunding for %s' % self.foia)
        self.crowdfund.foia.title = u'Test¢Unicode'
        self.crowdfund.foia.save()
        eq_('%s' % self.crowdfund, 'Crowdfunding for %s' % self.foia)

class TestCrowdfundProject(TestCase):
    """Test crowdfunding a project"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()
        self.project = self.crowdfund.project

    def test_unicode(self):
        """The crowdfund should express itself concisely."""
        eq_('%s' % self.crowdfund, 'Crowdfunding for Test Project')

    def test_unicode_characters(self):
        """The unicode method should support unicode characters"""
        project_title = u'Test¢s Request'
        self.project = Project.objects.create(title=project_title)
        self.crowdfund.project = self.project
        ok_('%s' % self.crowdfund)

    def test_get_crowdfund_object(self):
        """The crowdfund should have a project being crowdfunded."""
        eq_(self.crowdfund.get_crowdfund_object(), self.project)


class TestCrowdfundPayment(TestCase):
    """Test making a payment to a crowdfund"""

    def setUp(self):
        self.crowdfund = create_project_crowdfund()

    def test_make_payment(self):
        """Should make and return a payment object"""
        amount = Decimal(100)
        payment_object = self.crowdfund.make_payment(amount)
        ok_(isinstance(payment_object, models.CrowdfundProjectPayment),
            'Making a payment should create and return a payment object')
