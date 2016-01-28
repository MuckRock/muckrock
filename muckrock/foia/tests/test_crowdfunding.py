"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from django.core import mail
from django.test import TestCase, Client
import nose.tools

import datetime

from muckrock.crowdfund.models import Crowdfund
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.models import FOIARequest

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=no-member
# pylint: disable=missing-docstring
# pylint: disable=invalid-name

class TestFOIACrowdfunding(TestCase):
    """Tests for FOIA Crowdfunding"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        # pylint: disable=bad-super-call
        # pylint: disable=C0111

        mail.outbox = []
        self.user = User.objects.get(pk=1)
        self.foia = FOIARequest.objects.get(pk=18)
        self.url = reverse('foia-crowdfund', args=(
            self.foia.jurisdiction.slug,
            self.foia.jurisdiction.id,
            self.foia.slug,
            self.foia.id))
        self.client = Client()

    def form(self):
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        return response.context['form']

    def test_crowdfund_url(self):
        expected_url = (
            '/foi/' +
            self.foia.jurisdiction.slug + '-' + str(self.foia.jurisdiction.id) + '/' +
            self.foia.slug + '-' + str(self.foia.id) +
            '/crowdfund/'
        )
        nose.tools.eq_(self.url, expected_url,
            'Crowdfund URL <' + self.url + '> should match expected URL <' + expected_url + '>')

    def test_crowdfund_view(self):
        resolver = resolve(self.url)
        nose.tools.eq_(resolver.view_name, 'foia-crowdfund',
            'Crowdfund view name "' + resolver.view_name + '" should match "foia-crowdfund"')

    def test_crowdfund_view_requires_login(self):
        # client should be logged out
        response = self.client.get(self.url, follow=True)
        nose.tools.ok_(response,
            'Crowdfund should return a response object when issued a GET command')
        self.assertRedirects(response, '/accounts/login/?next=%s' % self.url)

    def test_crowdfund_view_requires_owner(self):
        # adam is the owner, not bob
        self.client.login(username='bob', password='abc')
        response = self.client.get(self.url)
        nose.tools.eq_(response.status_code, 302,
            ('Crowdfund should respond with a 302 redirect if logged in'
            ' user is not the owner. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_allows_staff(self):
        # adam is the owner, charles is staff
        self.client.login(username='charles', password='abc')
        response = self.client.get(self.url)
        nose.tools.eq_(response.status_code, 200,
            ('Crowdfund should respond with a 200 OK if logged in user'
            ' is a staff member. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_allows_owner(self):
        # adam is the owner
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        nose.tools.eq_(response.status_code, 200,
            ('Above all else crowdfund should totally respond with a 200 OK if'
            ' logged in user owns the request. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_crowdfund_already_exists(self):
        date_due = datetime.datetime.now() + datetime.timedelta(30)
        Crowdfund.objects.create(foia=self.foia, date_due=date_due)
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        nose.tools.eq_(response.status_code, 302,
            ('If a request already has a crowdfund, trying to create a new one '
            'should respond with 302 status code. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_payment_not_required(self):
        self.client.login(username='adam', password='abc')
        self.foia.status = 'submitted'
        self.foia.save()
        response = self.client.get(self.url)
        nose.tools.eq_(response.status_code, 302,
            ('If a request does not have a "Payment Required" status, should '
            'respond with a 302 status code. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_uses_correct_template(self):
        template = 'forms/foia/crowdfund.html'
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        nose.tools.ok_(template in [template.name for template in response.templates],
            ('Should render a form-based template for creating a crowdfund.'
            ' (Renders %s)' % response.templates))

    def test_crowdfund_view_uses_correct_form(self):
        form = self.form()
        nose.tools.eq_(form.__class__, CrowdfundForm,
            'View should use the CrowdfundForm')

    def test_crowdfund_view_form_has_initial_data(self):
        form = self.form()
        nose.tools.eq_(hasattr(form, 'initial'), True,
            'Every CrowdfundForm should have some initial data')

    def test_crowdfund_submit_with_initial_data(self):
        form = self.form()
        response = self.client.post(self.url, form.data)
        nose.tools.eq_(response.status_code, 200,
            'The crowdfund form should be submittable with just the initial data')
