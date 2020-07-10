# -*- coding: utf-8 -*-
"""Tests for the squarelet integration app"""

# Django
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

# Standard Library
import hashlib
import hmac
import time
import uuid

# Third Party
from mock import patch
from nose.tools import eq_

# MuckRock
from muckrock.squarelet.views import webhook


class ViewsTest(TestCase):
    """Test the squarelet webhook view"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.view = webhook
        self.url = reverse("squarelet-webhook")
        self.data = {
            "type": "user",
            "uuids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "timestamp": int(time.time()),
        }
        self.data["signature"] = self._calc_signature(
            self.data["timestamp"], self.data["type"], self.data["uuids"]
        )

    def _calc_signature(self, timestamp, type_, uuids):
        """Calculate the webhook signature"""
        return hmac.new(
            key=settings.SQUARELET_SECRET.encode("utf8"),
            msg="{}{}{}".format(timestamp, type_, "".join(uuids)).encode("utf8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    @patch("muckrock.squarelet.tasks.pull_data.delay")
    def test_webhook_success(self, mock):
        """Test a succesful webhook"""
        request = self.request_factory.post(self.url, self.data)
        response = self.view(request)

        eq_(response.status_code, 200)
        eq_(response.content, b"OK")
        for uuid_ in self.data["uuids"]:
            mock.assert_any_call(self.data["type"], uuid_)

    @patch("muckrock.squarelet.tasks.pull_data.delay")
    def test_webhook_signature_error(self, mock):
        """Test a webhook with an incorrect signature"""
        self.data["signature"] = "foobar"
        request = self.request_factory.post(self.url, self.data)
        response = self.view(request)

        eq_(response.status_code, 403)
        mock.assert_not_called()

    @patch("muckrock.squarelet.tasks.pull_data.delay")
    def test_webhook_expired_error(self, mock):
        """Test a webhook with an expired timestamp"""
        self.data["timestamp"] = int(time.time()) - 3600
        self.data["signature"] = self._calc_signature(
            self.data["timestamp"], self.data["type"], self.data["uuids"]
        )
        request = self.request_factory.post(self.url, self.data)
        response = self.view(request)

        eq_(response.status_code, 403)
        mock.assert_not_called()

    @patch("muckrock.squarelet.tasks.pull_data.delay")
    def test_webhook_bad_timestamp(self, mock):
        """Test a webhook with a non-numeric timestamp"""
        self.data["timestamp"] = "foobar"
        self.data["signature"] = self._calc_signature(
            self.data["timestamp"], self.data["type"], self.data["uuids"]
        )
        request = self.request_factory.post(self.url, self.data)
        response = self.view(request)

        eq_(response.status_code, 403)
        mock.assert_not_called()
