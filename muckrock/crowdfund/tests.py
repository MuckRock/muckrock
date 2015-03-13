"""
Tests for crowdfund app
"""

from django.test import TestCase

from mock import Mock
import nose.tools as _assert
from datetime import datetime, timedelta

from muckrock.crowdfund import models, forms
from muckrock.foia.models import FOIARequest

class TestCrowdfundRequestForm(TestCase):

    def setUp(self):
        pass

    def test_empty_request_form(self):
        form = forms.CrowdfundRequestForm()
        _assert.ok_(form)

