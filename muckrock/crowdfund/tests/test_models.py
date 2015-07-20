from django.test import TestCase

from datetime import date, timedelta
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.crowdfund import models

class TestCrowdfundProject(TestCase):
    """Test crowdfunding a project"""

    def setUp(self):
        self.project = Mock()
        self.project.title = 'Test Project'
        due_date = date.today() + timedelta(30)
        # create a crowdfund
        self.crowdfund = models.CrowdfundProject(
            name = 'Cool project please help',
            due_date = due_date,
            project = self.project
        )

    def test_unicode(self):
        eq_('%s' % self.crowdfund, 'Crowdfunding for Test Project')
