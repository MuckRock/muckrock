"""
Tests tasks for the Accounts application
"""

from django.test import TestCase

from nose.tools import eq_

from muckrock.accounts import models, tasks


class TestStatisticsTask(TestCase):
    """Statistics should be generated every day."""
    def test_stats(self):
        """A new statistic object should be generated."""
        # pylint: disable=no-self-use
        stat_count = models.Statistics.objects.count()
        tasks.store_statistics()
        new_stat_count = models.Statistics.objects.count()
        eq_(new_stat_count, stat_count + 1, 'A new Statistics object should be created.')
