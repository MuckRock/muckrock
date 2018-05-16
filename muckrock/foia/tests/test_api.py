"""
Test the FOIA API viewset
"""

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

# Standard Library
import json

# Third Party
import requests_mock
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.models import FOIAComposer


class TestFOIAViewsetCreate(TestCase):
    """Unit Tests for FOIA API Viewset create method"""

    def api_call(self, data=None, user_kwargs=None, code=201, status=None):
        """Helper for API calls"""
        if data is None:
            data = {}
        if 'agency' not in data:
            data['agency'] = AgencyFactory().pk,
        if 'title' not in data:
            data['title'] = 'Title'
        if 'document_request' not in data:
            data['document_request'] = 'Document Request'

        password = 'abc'
        user_kwargs_defaults = {
            'password': password,
            'profile__num_requests': 5,
        }
        if user_kwargs is not None:
            user_kwargs_defaults.update(user_kwargs)
        user = UserFactory.create(**user_kwargs_defaults)

        response = self.client.post(
            reverse('api-token-auth'),
            {'username': user.username,
             'password': password},
        )
        headers = {
            'content-type': 'application/json',
            'HTTP_AUTHORIZATION': 'Token %s' % response.json()['token'],
        }
        response = self.client.post(
            reverse('api-foia-list'),
            json.dumps(data),
            content_type='application/json',
            **headers
        )
        eq_(response.status_code, code, response)
        if status:
            eq_(response.json()['status'], status)

    @requests_mock.Mocker()
    def test_foia_create(self, mock):
        """Test creating a FOIA through the API"""
        attachment_url = 'http://www.example.com/attachment.txt'
        mock.get(
            attachment_url,
            headers={'Content-Type': 'text/plain'},
            text='Attachment content here',
        )
        agency = AgencyFactory()
        password = 'abc'
        user = UserFactory.create(
            password=password,
            profile__num_requests=5,
        )
        data = {
            'jurisdiction': agency.jurisdiction.pk,
            'agency': agency.pk,
            'document_request': 'The document',
            'title': 'Title',
            'attachments': [attachment_url],
        }
        response = self.client.post(
            reverse('api-token-auth'),
            {'username': user.username,
             'password': password},
        )
        headers = {
            'content-type': 'application/json',
            'HTTP_AUTHORIZATION': 'Token %s' % response.json()['token'],
        }
        response = self.client.post(
            reverse('api-foia-list'),
            json.dumps(data),
            content_type='application/json',
            **headers
        )
        eq_(response.status_code, 201, response)

    def test_simple(self):
        """Test with bare minimum data supplied"""
        self.api_call()

    def test_multi_agency(self):
        """Test with multiple agencies"""
        agencies = AgencyFactory.create_batch(3)
        self.api_call({'agency': [a.pk for a in agencies]})

    def test_bad_agency_id_format(self):
        """Test with a bad agency ID format"""
        self.api_call(
            {
                'agency': 'foo',
            },
            code=400,
            status='Bad agency ID format',
        )

    def test_no_agency(self):
        """Test with no agency given"""
        self.api_call(
            {
                'agency': [],
            },
            code=400,
            status='At least one valid agency required',
        )

    def test_bad_agency(self):
        """Test with bad agency ID given"""
        self.api_call(
            {
                'agency': 123,
            },
            code=400,
            status='At least one valid agency required',
        )

    def test_embargo(self):
        """Test embargoing"""
        self.api_call(
            {
                'embargo': True,
            },
            user_kwargs={
                'profile__acct_type': 'pro',
            },
        )
        composer = FOIAComposer.objects.get()
        assert_true(composer.embargo)
        assert_false(composer.permanent_embargo)

    def test_embargo_bad(self):
        """Test embargoing without permissions"""
        self.api_call(
            {
                'embargo': True,
            },
            user_kwargs={
                'profile__acct_type': 'basic',
            },
            code=400,
            status='You do not have permission to embargo requests',
        )

    def test_permanent_embargo(self):
        """Test permanent embargoing"""
        self.api_call(
            {
                'permanent_embargo': True,
            },
            user_kwargs={
                'profile__acct_type': 'admin',
            },
        )
        composer = FOIAComposer.objects.get()
        ok_(composer.embargo)
        ok_(composer.permanent_embargo)

    def test_permanent_embargo_bad(self):
        """Test permanent embargoing without permissions"""
        self.api_call(
            {
                'permanent_embargo': True,
            },
            user_kwargs={
                'profile__acct_type': 'pro',
            },
            code=400,
            status='You do not have permission to permanently embargo requests',
        )

    def test_no_title(self):
        """Test missing title"""
        self.api_call(
            {
                'title': '',
            },
            code=400,
            status='title required',
        )

    def test_no_document_request(self):
        """Test missing document request"""
        self.api_call(
            {
                'document_request': '',
            },
            code=400,
            status='document_request or full_text required',
        )

    @requests_mock.Mocker()
    def test_attachments(self, mock):
        """Test attachments"""
        mock.get(
            'http://www.example.com/attachment.txt',
            headers={'Content-Type': 'text/plain'},
            text='Attachment content here',
        )
        mock.get(
            'http://www.example.com/attachment.pdf',
            headers={'Content-Type': 'application/pdf'},
            text='Attachment content here',
        )
        self.api_call({
            'attachments': [
                'http://www.example.com/attachment.txt',
                'http://www.example.com/attachment.pdf',
            ],
        })
        composer = FOIAComposer.objects.get()
        eq_(composer.pending_attachments.count(), 2)

    def test_attachments_bad_format(self):
        """Test attachments not given as a list"""
        self.api_call(
            {
                'attachments': 'http://www.example.com/attachment.txt',
            },
            code=400,
            status='attachments should be a list of publicly available URLs',
        )

    @requests_mock.Mocker()
    def test_attachments_bad_mime(self, mock):
        """Test attachments with a bad mime type"""
        url = 'http://www.example.com/attachment.exe'
        mock.get(
            url,
            headers={'Content-Type': 'application/octet-stream'},
            text='Attachment content here',
        )
        self.api_call(
            {
                'attachments': [url],
            },
            code=400,
            status=
            'Attachment: {} is not of a valid mime type.  Valid types include: {}'.
            format(url, ', '.join(settings.ALLOWED_FILE_MIMES)),
        )

    def test_attachments_bad_url(self):
        """Test attachments with a bad URL"""
        url = 'foo'
        self.api_call(
            {
                'attachments': [url],
            },
            code=400,
            status='Error downloading attachment: {}'.format(url),
        )

    @requests_mock.Mocker()
    def test_attachments_error_url(self, mock):
        """Test attachments with an error URL"""
        url = 'http://www.example.com/attachment.html'
        mock.get(
            url,
            headers={'Content-Type': 'text/html'},
            status_code=404,
        )
        self.api_call(
            {
                'attachments': [url],
            },
            code=400,
            status='Error downloading attachment: {}, code: {}'.format(
                url, 404
            ),
        )

    def test_no_requests(self):
        """Test submitting when out of requests"""
        self.api_call(
            user_kwargs={
                'profile__num_requests': 0,
            },
            code=402,
            status='Out of requests.  FOI Request has been saved.',
        )
