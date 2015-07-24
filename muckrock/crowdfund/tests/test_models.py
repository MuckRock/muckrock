"""
Tests for crowdfunding models
"""

from django.test import TestCase

from datetime import date, timedelta
from nose.tools import eq_

from muckrock.crowdfund import models
from muckrock.project.models import Project

class TestCrowdfundProject(TestCase):
    """Test crowdfunding a project"""

    def setUp(self):
        self.crowdfund = models.CrowdfundProject()
        self.crowdfund.name = 'Cool project please help'
        self.crowdfund.due_date = date.today() + timedelta(30)
        self.project = Project.objects.create(title='Test Project')
        self.crowdfund.project = self.project

    def test_unicode(self):
        """The crowdfund should express itself concisely."""
        eq_('%s' % self.crowdfund, 'Crowdfunding for Test Project')

    def test_get_crowdfund_object(self):
        """The crowdfund should have a project being crowdfunded."""
        eq_(self.crowdfund.get_crowdfund_object(), self.project)
