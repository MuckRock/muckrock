"""
Tests tasks for the Accounts application
"""

# Django
from django.test import TestCase

# MuckRock
from muckrock.accounts import models, tasks


class TestStatisticsTask(TestCase):
    """Statistics should be generated every day."""

    def test_stats(self):
        """A new statistic object should be generated."""
        stat_count = models.Statistics.objects.count()
        tasks.store_statistics()
        new_stat_count = models.Statistics.objects.count()
        assert (
            new_stat_count == stat_count + 1
        ), "A new Statistics object should be created."
