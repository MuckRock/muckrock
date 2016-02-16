"""
Test recurring crowdfund tasks
"""

from django import test

from datetime import date, timedelta
from nose.tools import ok_

from muckrock.crowdfund import models, tasks
from muckrock.project.models import Project

class TestRecurringTasks(test.TestCase):
    """Test recurring crowdfund tasks"""
    def setUp(self):
        self.project = Project.objects.create(title='Cool project')

    def test_close_expired(self):
        """Projects past their due date should be closed"""
        crowdfund = models.Crowdfund.objects.create(
            name='Cool project please help',
            date_due=(date.today() - timedelta(1)),
            payment_required=20.00,
        )
        tasks.close_expired()
        updated_crowdfund = models.Crowdfund.objects.get(pk=crowdfund.pk)
        ok_(updated_crowdfund.closed, 'Any crowdfund past its date due should be closed.')

    def test_do_not_close_today(self):
        """Projects with a due date of today should not be clsoed."""
        crowdfund = models.Crowdfund.objects.create(
            name='Cool project please help',
            date_due=(date.today()),
            payment_required=20.00,
        )
        crowdfund.save()
        tasks.close_expired()
        updated_crowdfund = models.Crowdfund.objects.get(pk=crowdfund.pk)
        ok_(not updated_crowdfund.closed,
            'Crowdfunds with a due date of today should not be closed.')
