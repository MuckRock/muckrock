# -*- coding: utf-8 -*-
"""
Tests for when a repair closes the agency level task

An agency level task covers every channel, so it is done only once no broken
channel at the agency still carries open requests.
"""

# Django
from django.test import TestCase

# Standard Library
from unittest import mock

# MuckRock
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.tests.test_repair import ChannelRepairMixin


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestAgencyLevelResolve(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """The agency level task closes once no broken channel is left"""

    def agency_task(self):
        return ReviewAgencyTaskFactory(agency=self.agency, email=None, resolved=False)

    def test_stays_open_while_another_broken_channel_carries_requests(
        self, _mock_delay
    ):
        """Found in local testing: Jacksonville's closed with 16 still blocked"""
        first, first_foias, _first_task = self.make_channel("one@agency.gov")
        self.make_channel("two@agency.gov", blocked=3, request_type="none")
        agency_task = self.agency_task()
        self.post(
            new_email="new@agency.gov",
            channel_pks=str(first.pk),
            foia_pks=str(first_foias[0].pk),
            resolve="on",
        )
        agency_task.refresh_from_db()
        assert not agency_task.resolved

    def test_closes_once_every_broken_channel_is_repaired(self, _mock_delay):
        first, first_foias, _first_task = self.make_channel("one@agency.gov")
        second, second_foias, _second_task = self.make_channel(
            "two@agency.gov", request_type="none"
        )
        agency_task = self.agency_task()
        self.post(
            new_email="new@agency.gov",
            channel_pks="%d,%d" % (first.pk, second.pk),
            foia_pks=",".join(str(f.pk) for f in first_foias + second_foias),
            resolve="on",
        )
        agency_task.refresh_from_db()
        assert agency_task.resolved
