"""
Tests for fine uploader integration
"""

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Standard Library
import json

# Third Party
from nose.tools import assert_false, eq_

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.fine_uploader import views
from muckrock.foia.factories import FOIARequestFactory, OutboundRequestAttachmentFactory
from muckrock.foia.models import OutboundRequestAttachment


class TestFineUploaderSuccessView(TestCase):
    """Tests for fine uploader success view"""

    def test_success_success(self):
        """Test a successful post to the success view"""
        foia = FOIARequestFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-success-request"), {"id": foia.pk, "key": "file_key"}
        )
        request.user = foia.user
        response = views.success_request(request)
        eq_(response.status_code, 200)
        attachment = OutboundRequestAttachment.objects.get(foia=foia)
        eq_(attachment.ffile.name, "file_key")
        eq_(attachment.user, foia.user)
        assert_false(attachment.sent)

    def test_success_bad_comm(self):
        """Test a post to the success view with a non-existent foia"""
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-success-request"), {"id": 1234, "key": "file_key"}
        )
        request.user = UserFactory()
        response = views.success_request(request)
        eq_(response.status_code, 400)

    def test_success_bad_user(self):
        """Test a post to the success view with a bad user"""
        foia = FOIARequestFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-success-request"), {"id": foia.pk, "key": "file_key"}
        )
        request.user = UserFactory()
        response = views.success_request(request)
        eq_(response.status_code, 403)

    def test_success_bad_data(self):
        """Test a post to the success view with missing data"""
        foia = FOIARequestFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-success-request"), {"id": foia.pk}
        )
        request.user = foia.user
        response = views.success_request(request)
        eq_(response.status_code, 400)


class TestFineUploaderSessionView(TestCase):
    """Tests for fine uploader session view"""

    def test_session_success(self):
        """Test a successful post to the session view"""
        foia = FOIARequestFactory()
        attachments = OutboundRequestAttachmentFactory.create_batch(
            3, foia=foia, user=foia.user, sent=False
        )
        OutboundRequestAttachmentFactory.create_batch(
            3, foia=foia, user=foia.user, sent=True
        )
        OutboundRequestAttachmentFactory.create_batch(3)
        request_factory = RequestFactory()
        request = request_factory.get(
            reverse("fine-uploader-session-request"), {"id": foia.pk}
        )
        request.user = foia.user
        response = views.session_request(request)
        eq_(response.status_code, 200)
        attm_data = json.loads(response.content)
        attm_data.sort(key=lambda f: f["uuid"])
        attachments.sort(key=lambda f: f.pk)
        for attm_datum, attm in zip(attm_data, attachments):
            eq_(attm_datum["name"], attm.name())
            eq_(attm_datum["uuid"], attm.pk)
            eq_(attm_datum["size"], attm.ffile.size)
            eq_(attm_datum["s3Key"], attm.ffile.name)

    def test_session_bad_comm(self):
        """Test a post to the session view with a non-existent foia"""
        request_factory = RequestFactory()
        request = request_factory.get(
            reverse("fine-uploader-session-request"), {"id": 1234}
        )
        request.user = UserFactory()
        response = views.session_request(request)
        eq_(response.status_code, 400)

    def test_session_bad_user(self):
        """Test a post to the session view with a bad user"""
        foia = FOIARequestFactory()
        request_factory = RequestFactory()
        request = request_factory.get(
            reverse("fine-uploader-session-request"),
            {"id": foia.pk, "name": "file_name", "key": "file_key"},
        )
        request.user = UserFactory()
        response = views.session_request(request)
        eq_(response.status_code, 403)


class TestFineUploaderDeleteView(TestCase):
    """Tests for fine uploader delete view"""

    def test_delete_success(self):
        """Test a successful post to the delete view"""
        attm = OutboundRequestAttachmentFactory()

        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-delete-request", kwargs={"idx": attm.pk})
        )
        request.user = attm.user
        response = views.delete_request(request, attm.pk)
        eq_(response.status_code, 200)
        assert_false(OutboundRequestAttachment.objects.filter(pk=attm.pk).exists())

    def test_delete_bad_file(self):
        """Test a post to the delete view with a non-existent file"""
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-delete-request", kwargs={"idx": 123456})
        )
        request.user = UserFactory()
        response = views.delete_request(request, 123456)
        eq_(response.status_code, 400)

    def test_delete_bad_user(self):
        """Test a post to the delete view with a bad user"""
        attm = OutboundRequestAttachmentFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse("fine-uploader-delete-request", kwargs={"idx": attm.pk})
        )
        request.user = UserFactory()
        attm.user = request.user
        attm.save()
        response = views.delete_request(request, attm.pk)
        eq_(response.status_code, 403)


class TestFineUploaderSignView(TestCase):
    """Tests for fine uploader delete view"""


class TestFineUploaderKeyView(TestCase):
    """Tests for fine uploader delete view"""


class TestFineUploaderBlankView(TestCase):
    """Tests for fine uploader blank view"""

    def test_blank(self):
        """Test the blank view"""
        request_factory = RequestFactory()
        request = request_factory.get(reverse("fine-uploader-blank"))
        request.user = UserFactory()
        response = views.blank(request)
        eq_(response.status_code, 200)
