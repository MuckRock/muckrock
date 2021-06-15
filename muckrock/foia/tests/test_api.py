"""
Test the FOIA API viewset
"""

# Django
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

# Standard Library
import json
import re

# Third Party
import requests_mock
from nose.tools import assert_false, assert_true, eq_, ok_
from rest_framework.authtoken.models import Token

# MuckRock
from muckrock.core.factories import (
    AgencyFactory,
    OrganizationUserFactory,
    ProfessionalUserFactory,
    UserFactory,
)
from muckrock.core.test_utils import mock_squarelet
from muckrock.foia.factories import FOIATemplateFactory
from muckrock.foia.models import FOIAComposer


class TestFOIAViewsetCreate(TestCase):
    """Unit Tests for FOIA API Viewset create method"""

    def setUp(self):
        self.mocker = requests_mock.Mocker()
        mock_squarelet(self.mocker)
        self.mocker.start()
        self.addCleanup(self.mocker.stop)
        FOIATemplateFactory.create()

    def api_call(
        self, data=None, user_type=None, number_requests=5, code=201, status=None
    ):
        """Helper for API calls"""
        # pylint: disable=too-many-arguments
        if data is None:
            data = {}
        if "agency" not in data:
            data["agency"] = (AgencyFactory().pk,)
        if "title" not in data:
            data["title"] = "Title"
        if "document_request" not in data:
            data["document_request"] = "Document Request"

        user_factory = {
            None: UserFactory,
            "pro": ProfessionalUserFactory,
            "org": OrganizationUserFactory,
        }[user_type]
        user = user_factory.create(
            membership__organization__number_requests=number_requests
        )
        Token.objects.create(user=user)

        headers = {
            "content-type": "application/json",
            "HTTP_AUTHORIZATION": "Token %s" % user.auth_token,
        }
        response = self.client.post(
            reverse("api-foia-list"),
            json.dumps(data),
            content_type="application/json",
            **headers
        )
        eq_(
            response.status_code,
            code,
            "Code: {}\nResponse: {}".format(response.status_code, response),
        )
        if status:
            eq_(response.json()["status"], status)

        return response

    def test_foia_create(self):
        """Test creating a FOIA through the API"""
        attachment_url = "http://www.example.com/attachment.txt"
        self.mocker.get(
            attachment_url,
            headers={"Content-Type": "text/plain"},
            text="Attachment content here",
        )
        agency = AgencyFactory()
        user = UserFactory.create(membership__organization__number_requests=5)
        Token.objects.create(user=user)
        data = {
            "jurisdiction": agency.jurisdiction.pk,
            "agency": agency.pk,
            "document_request": "The document",
            "title": "Title",
            "attachments": [attachment_url],
        }
        headers = {
            "content-type": "application/json",
            "HTTP_AUTHORIZATION": "Token %s" % user.auth_token,
        }
        response = self.client.post(
            reverse("api-foia-list"),
            json.dumps(data),
            content_type="application/json",
            **headers
        )
        eq_(response.status_code, 201, response)
        eq_(len(response.json()["Requests"]), 1)

    def test_simple(self):
        """Test with bare minimum data supplied"""
        self.api_call()

    def test_multi_agency(self):
        """Test with multiple agencies"""
        agencies = AgencyFactory.create_batch(3)
        response = self.api_call({"agency": [a.pk for a in agencies]})
        eq_(len(response.json()["Requests"]), 3)

    def test_bad_agency_id_format(self):
        """Test with a bad agency ID format"""
        self.api_call({"agency": "foo"}, code=400, status="Bad agency ID format")

    def test_no_agency(self):
        """Test with no agency given"""
        self.api_call(
            {"agency": []}, code=400, status="At least one valid agency required"
        )

    def test_bad_agency(self):
        """Test with bad agency ID given"""
        self.api_call(
            {"agency": 123}, code=400, status="At least one valid agency required"
        )

    def test_embargo(self):
        """Test embargoing"""
        self.api_call({"embargo": True}, user_type="pro")
        composer = FOIAComposer.objects.get()
        assert_true(composer.embargo)
        assert_false(composer.permanent_embargo)

    def test_embargo_bad(self):
        """Test embargoing without permissions"""
        self.api_call(
            {"embargo": True},
            code=400,
            status="You do not have permission to embargo requests",
        )

    def test_permanent_embargo(self):
        """Test permanent embargoing"""
        self.api_call({"permanent_embargo": True}, user_type="org")
        composer = FOIAComposer.objects.get()
        ok_(composer.embargo)
        ok_(composer.permanent_embargo)

    def test_permanent_embargo_bad(self):
        """Test permanent embargoing without permissions"""
        self.api_call(
            {"permanent_embargo": True},
            user_type="pro",
            code=400,
            status="You do not have permission to permanently embargo requests",
        )

    def test_no_title(self):
        """Test missing title"""
        self.api_call({"title": ""}, code=400, status="title required")

    def test_no_document_request(self):
        """Test missing document request"""
        self.api_call(
            {"document_request": ""},
            code=400,
            status="document_request or full_text required",
        )

    def test_attachments(self):
        """Test attachments"""
        self.mocker.get(
            "http://www.example.com/attachment.txt",
            headers={"Content-Type": "text/plain"},
            text="Attachment content here",
        )
        self.mocker.get(
            "http://www.example.com/attachment.pdf",
            headers={"Content-Type": "application/pdf"},
            text="Attachment content here",
        )
        self.api_call(
            {
                "attachments": [
                    "http://www.example.com/attachment.txt",
                    "http://www.example.com/attachment.pdf",
                ]
            }
        )
        composer = FOIAComposer.objects.get()
        eq_(composer.pending_attachments.count(), 2)

    def test_attachments_bad_format(self):
        """Test attachments not given as a list"""
        self.api_call(
            {"attachments": "http://www.example.com/attachment.txt"},
            code=400,
            status="attachments should be a list of publicly available URLs",
        )

    def test_attachments_bad_mime(self):
        """Test attachments with a bad mime type"""
        url = "http://www.example.com/attachment.exe"
        self.mocker.get(
            url,
            headers={"Content-Type": "application/octet-stream"},
            text="Attachment content here",
        )
        self.api_call(
            {"attachments": [url]},
            code=400,
            status="Attachment: {} is not of a valid mime type.  Valid types include: {}".format(
                url, ", ".join(settings.ALLOWED_FILE_MIMES)
            ),
        )

    def test_attachments_bad_url(self):
        """Test attachments with a bad URL"""
        url = "foo"
        self.api_call(
            {"attachments": [url]},
            code=400,
            status="Error downloading attachment: {}".format(url),
        )

    def test_attachments_error_url(self):
        """Test attachments with an error URL"""
        url = "http://www.example.com/attachment.html"
        self.mocker.get(url, headers={"Content-Type": "text/html"}, status_code=404)
        self.api_call(
            {"attachments": [url]},
            code=400,
            status="Error downloading attachment: {}, code: {}".format(url, 404),
        )

    def test_no_requests(self):
        """Test submitting when out of requests"""
        self.mocker.post(
            re.compile(
                r"{}/api/organizations/[a-f0-9-]+/requests/".format(
                    settings.SQUARELET_URL
                )
            ),
            json={"extra": 1},
            status_code=402,
        )
        self.api_call(
            number_requests=0,
            code=402,
            status="Out of requests.  FOI Request has been saved.",
        )
