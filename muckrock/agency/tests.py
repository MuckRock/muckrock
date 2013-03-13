"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_agencies.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency = Agency.objects.get(pk=1)

    def test_agency_unicode(self):
        """Test Agency model's __unicode__ method"""
        nose.tools.eq_(unicode(self.agency), u'Test Agency')

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        nose.tools.eq_(self.agency.get_absolute_url(),
            reverse('agency-detail', kwargs={'idx': self.agency.pk, 'slug': 'test-agency',
                                             'jurisdiction': 'cambridge-ma',
                                             'jidx': self.agency.jurisdiction.pk}))

    def test_agency_normalize_fax(self):
        """Test the normalize fax method"""
        nose.tools.eq_(Agency.objects.get(pk=1).normalize_fax(), '19876543210')
        nose.tools.eq_(Agency.objects.get(pk=2).normalize_fax(), '19876543210')
        nose.tools.eq_(Agency.objects.get(pk=3).normalize_fax(), None)

    def test_agency_get_email(self):
        """Test the get email method"""
        nose.tools.eq_(Agency.objects.get(pk=1).get_email(), 'test@agency1.gov')
        nose.tools.eq_(Agency.objects.get(pk=2).get_email(), '19876543210@fax2.faxaway.com')
        nose.tools.eq_(Agency.objects.get(pk=3).get_email(), '')

    def test_agency_get_other_emails(self):
        """Test get other emails method"""
        nose.tools.eq_(self.agency.get_other_emails(),
                       ['other_a@agency1.gov', 'other_b@agency1.gov'])

class TestAgencyViews(TestCase):
    """Tests for Agency views"""
    fixtures = ['test_users.json', 'jurisdictions.json', 'agency_types.json', 'test_agencies.json',
                'test_foiarequests.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency = Agency.objects.get(pk=1)

    def test_detail(self):
        """Test the detail view"""

        get_allowed(self.client,
                    reverse('agency-detail',
                            kwargs={'jurisdiction': self.agency.jurisdiction.slug,
                                    'jidx': self.agency.jurisdiction.pk,
                                    'slug': self.agency.slug, 'idx': self.agency.pk}),
                    ['agency/agency_detail.html', 'agency/base.html'],
                    context={'agency': self.agency})

        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': 'fake-jurisdiction',
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': self.agency.slug, 'idx': self.agency.pk}))
        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': self.agency.jurisdiction.slug,
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': 'fake-slug', 'idx': self.agency.pk}))

        agency = Agency.objects.get(pk=3)
        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': agency.jurisdiction.slug,
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': agency.slug, 'idx': agency.pk}))

    def test_update(self):
        """Test the update view"""

        agency = Agency.objects.get(pk=3)

        get_post_unallowed(self.client,
                           reverse('agency-update',
                                   kwargs={'jurisdiction': agency.jurisdiction.slug,
                                           'jidx': agency.jurisdiction.pk,
                                           'slug': agency.slug, 'idx': agency.pk}))

        self.client.login(username='adam', password='abc')
        get_allowed(self.client,
                    reverse('agency-update',
                            kwargs={'jurisdiction': agency.jurisdiction.slug,
                                    'jidx': agency.jurisdiction.pk,
                                    'slug': agency.slug, 'idx': agency.pk}),
                    ['agency/agency_form.html', 'agency/base.html'])

        get_allowed(self.client,
                    reverse('agency-update',
                            kwargs={'jurisdiction': self.agency.jurisdiction.slug,
                                    'jidx': self.agency.jurisdiction.pk,
                                    'slug': self.agency.slug, 'idx': self.agency.pk}),
                    redirect=reverse('foia-mylist', kwargs={'view': 'all'}))

        get_404(self.client, reverse('agency-update',
                                     kwargs={'jurisdiction': agency.jurisdiction.slug,
                                             'jidx': agency.jurisdiction.pk,
                                             'slug': 'fake-slug', 'idx': agency.pk}))

        post_allowed_bad(self.client,
                         reverse('agency-update',
                                 kwargs={'jurisdiction': agency.jurisdiction.slug,
                                         'jidx': agency.jurisdiction.pk,
                                         'slug': agency.slug, 'idx': agency.pk}),
                         ['agency/agency_form.html', 'agency/base.html'])

        agency_data = {'name': agency.name,
                       'jurisdiction': agency.jurisdiction.pk,
                       'address': agency.address,
                       'email': 'test@example.com',
                       'url': agency.url,
                       'phone': agency.phone,
                       'fax': agency.fax,
                      }
        post_allowed(self.client,
                     reverse('agency-update',
                             kwargs={'jurisdiction': agency.jurisdiction.slug,
                                     'jidx': agency.jurisdiction.pk,
                                     'slug': agency.slug, 'idx': agency.pk}),
                     agency_data, reverse('foia-mylist', kwargs={'view': 'all'}))
        foia = FOIARequest.objects.get(pk=1)
        post_allowed(self.client,
                     reverse('agency-update',
                             kwargs={'jurisdiction': agency.jurisdiction.slug,
                                     'jidx': agency.jurisdiction.pk,
                                     'slug': agency.slug, 'idx': agency.pk})
                     + '?foia=%d' % foia.pk,
                     agency_data, foia.get_absolute_url())
        agency = Agency.objects.get(pk=3)
        nose.tools.eq_(agency.email, 'test@example.com')
