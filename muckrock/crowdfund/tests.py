"""
Tests for crowdfund app
"""

from django.test import TestCase

from mock import Mock
import nose.tools as _assert
from datetime import datetime, timedelta

from muckrock.crowdfund import forms
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.models import FOIARequest

class TestCrowdfundRequestForm(TestCase):

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        pass

    def test_empty_request_form(self):
        form = forms.CrowdfundRequestForm()
        _assert.ok_(form)

    def test_prefilled_request_form(self):
        foia = FOIARequest.objects.get(pk=1)
        due = datetime.now() + timedelta(30)
        crowdfund = CrowdfundRequest.objects.create(foia=foia, date_due=due)
        form = forms.CrowdfundRequestForm(instance=crowdfund)
        _assert.ok_(form)
