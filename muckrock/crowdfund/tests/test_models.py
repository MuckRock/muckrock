from django.test import TestCase

from datetime import date, timedelta
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.crowdfund import models
from muckrock.project.models import Project

class TestCrowdfundProject(TestCase):
    """Test crowdfunding a project"""

    def setUp(self):
        self.crowdfund = models.CrowdfundProject()
        self.crowdfund.name = 'Cool project please help'
        self.crowdfund.due_date = date.today() + timedelta(30)
        project = Project.objects.create(title='Test Project')
        self.crowdfund.project = project

    def test_unicode(self):
        eq_('%s' % self.crowdfund, 'Crowdfunding for Test Project')
