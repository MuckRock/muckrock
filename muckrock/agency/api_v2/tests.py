from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from muckrock.agency.models import Agency, Jurisdiction
from muckrock.core.factories import UserFactory, AgencyFactory, JurisdictionFactory

class AgencyViewSetTests(APITestCase):

    def setUp(self):
        # Create test jurisdictions
        self.jurisdiction = JurisdictionFactory.create(name='1st Jurisdiction')
        self.jurisdiction2 = JurisdictionFactory.create(name="2nd Jurisdiction")
        
        # Create agencies
        self.approved_agency = AgencyFactory.create(
            name='First Approved Agency',
            jurisdiction=self.jurisdiction,
            status='approved'
        )
        self.unapproved_agency = AgencyFactory.create(
            name='Unapproved Agency',
            jurisdiction=self.jurisdiction,
            status='unapproved'
        )
        self.approved_agency2 = AgencyFactory.create(
            name="Second Approved Agency",
            jurisdiction=self.jurisdiction2,
            status='approved'
        )

        # URL for the agency list
        self.url = reverse('agency-list')

    def test_retrieve_agencies(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fuzzy_search_agency_name(self):
        response = self.client.get(self.url, {'search': 'Second'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        agency_names = [agency['name'] for agency in response_data['results']]
        
        self.assertIn('Second Approved Agency', agency_names)
        self.assertNotIn('First Approved Agency', agency_names)
        self.assertNotIn('Unapproved Agency', agency_names)

    def test_fuzzy_search_jurisdiction_name(self):
        response = self.client.get(self.url, {'search': '1st'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        agency_names = [agency['name'] for agency in response_data['results']]
        
        self.assertNotIn('Second Approved Agency', agency_names)

    def test_non_approved_agencies_hidden(self):
        self.client.logout()  # Ensure we're not logged in as staff
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        agency_names = [agency['name'] for agency in response_data['results']]
        
        self.assertIn('First Approved Agency', agency_names)
        self.assertNotIn('Unapproved Agency', agency_names)

    def test_staff_user_can_see_all_agencies(self):
        user = UserFactory.create(is_staff=True)
        self.client.force_authenticate(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        agency_names = [agency['name'] for agency in response_data['results']]
        
        self.assertIn('First Approved Agency', agency_names)
        self.assertIn('Second Approved Agency', agency_names)
        self.assertIn('Unapproved Agency', agency_names)

    def test_ordering(self):
        response = self.client.get(self.url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency['name'] for agency in response_data['results']]
        
        # Assuming the expected order based on names
        self.assertEqual(agency_names, ['First Approved Agency', 'Second Approved Agency', 'Unapproved Agency'])
