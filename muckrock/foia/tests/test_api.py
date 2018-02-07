"""
Test the FOIA API viewset
"""

# Django
from django.core.urlresolvers import reverse
from django.test import TestCase

# Standard Library
import json

# Third Party
import nose.tools
import requests_mock

# MuckRock
from muckrock.factories import AgencyFactory, UserFactory


class TestFOIAViewset(TestCase):
    """Unit Tests for FOIA API Viewset"""

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
        nose.tools.eq_(response.status_code, 201, response)
