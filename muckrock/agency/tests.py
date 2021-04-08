"""
Tests for Agency application
"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Standard Library
import json

# Third Party
from nose.tools import assert_in, assert_not_in, eq_, ok_, raises

# MuckRock
from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock.agency.views import AgencyList, boilerplate, contact_info, detail
from muckrock.communication.factories import EmailAddressFactory, PhoneNumberFactory
from muckrock.core.factories import (
    AgencyEmailFactory,
    AgencyFactory,
    AgencyPhoneFactory,
    ProfessionalUserFactory,
    UserFactory,
)
from muckrock.core.test_utils import http_get_response, mock_middleware
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory


class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""

    def setUp(self):
        """Set up tests"""
        self.agency1 = AgencyFactory(
            fax__phone__number="1-987-654-3211",
            email__email__email="test@agency1.gov",
            other_emails="other_a@agency1.gov, other_b@agency1.gov",
        )
        self.agency2 = AgencyFactory(fax__phone__number="987.654.3210")
        self.agency3 = AgencyFactory(email=None)

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        eq_(
            self.agency1.get_absolute_url(),
            reverse(
                "agency-detail",
                kwargs={
                    "idx": self.agency1.pk,
                    "slug": self.agency1.slug,
                    "jurisdiction": self.agency1.jurisdiction.slug,
                    "jidx": self.agency1.jurisdiction.pk,
                },
            ),
        )

    def test_agency_get_email(self):
        """Test the get emails method"""
        eq_(self.agency1.get_emails().first().email, "test@agency1.gov")
        eq_(self.agency3.get_emails().first(), None)

    def test_agency_get_faxes(self):
        """Test the ganecy get faces method"""
        eq_(self.agency2.get_faxes().first().number, "19876543210")

    def test_agency_get_emails(self):
        """Test get emails method"""
        eq_(
            set(e.email for e in self.agency1.get_emails(email_type="cc")),
            set(["other_a@agency1.gov", "other_b@agency1.gov"]),
        )

    def test_agency_get_proxy_info(self):
        """Test an agencies get_proxy_info method"""
        agency_ = AgencyFactory()
        proxy_info = agency_.get_proxy_info()
        eq_(proxy_info["proxy"], False)
        eq_(proxy_info["missing_proxy"], False)
        assert_not_in("from_user", proxy_info)
        assert_not_in("warning", proxy_info)

        agency_ = AgencyFactory(requires_proxy=True)
        proxy_info = agency_.get_proxy_info()
        eq_(proxy_info["proxy"], True)
        eq_(proxy_info["missing_proxy"], True)
        assert_not_in("from_user", proxy_info)
        assert_in("warning", proxy_info)

        proxy = UserFactory(
            profile__proxy=True, profile__state=agency_.jurisdiction.legal.abbrev
        )
        proxy_info = agency_.get_proxy_info()
        eq_(proxy_info["proxy"], True)
        eq_(proxy_info["missing_proxy"], False)
        eq_(proxy_info["from_user"], proxy)
        assert_in("warning", proxy_info)

    def test_agency_relations(self):
        """Pins the number of relations
        If we add a relation we must take into account how we want to handle it during
        a merge
        """
        # Relations pointing to the Agency model
        eq_(
            len(
                [
                    f
                    for f in Agency._meta.get_fields()
                    if f.is_relation and f.auto_created
                ]
            ),
            16,
        )
        # Many to many relations defined on the agency model
        eq_(
            len(
                [
                    f
                    for f in Agency._meta.get_fields()
                    if f.many_to_many and not f.auto_created
                ]
            ),
            4,
        )

    def test_agency_merge(self):
        """Test agency merging"""
        good_agency = AgencyFactory(status="approved", email=None, fax=None)
        bad_agency = AgencyFactory(status="approved", email=None, fax=None)
        appeal_agency = AgencyFactory(appeal_agency=bad_agency)
        foia = FOIARequestFactory(agency=bad_agency)
        composer = FOIAComposerFactory(agencies=[bad_agency])
        user = UserFactory()

        email = EmailAddressFactory()
        AgencyEmailFactory(agency=good_agency, email=email, email_type="to")
        AgencyEmailFactory(agency=bad_agency, email=email, email_type="cc")

        fax1 = PhoneNumberFactory()
        fax2 = PhoneNumberFactory()
        AgencyPhoneFactory(agency=good_agency, phone=fax1, request_type="primary")
        AgencyPhoneFactory(agency=bad_agency, phone=fax2, request_type="primary")

        good_agency.merge(bad_agency, user)

        bad_agency.refresh_from_db()
        appeal_agency.refresh_from_db()
        foia.refresh_from_db()
        composer.refresh_from_db()

        eq_(bad_agency.status, "rejected")
        eq_(foia.agency, good_agency)
        eq_(composer.agencies.first(), good_agency)
        eq_(appeal_agency.appeal_agency, good_agency)

        # email that already exists is not copied over
        eq_(good_agency.emails.count(), 1)
        eq_(good_agency.agencyemail_set.first().email_type, "to")

        # phone number that doesnt exist is copied over
        eq_(good_agency.phones.count(), 2)
        # existing phone number is unaffected
        ok_(
            good_agency.agencyphone_set.filter(
                phone=fax1, request_type="primary"
            ).exists()
        )
        # its type is set to none when copied over
        ok_(
            good_agency.agencyphone_set.filter(phone=fax2, request_type="none").exists()
        )

        assert_in(good_agency.name, bad_agency.notes)
        assert_in(str(good_agency.pk), bad_agency.notes)
        assert_in(user.username, bad_agency.notes)


class TestAgencyManager(TestCase):
    """Tests for the Agency object manager"""

    def setUp(self):
        self.agency1 = AgencyFactory()
        self.agency2 = AgencyFactory(jurisdiction=self.agency1.jurisdiction)
        self.agency3 = AgencyFactory(
            jurisdiction=self.agency1.jurisdiction, status="pending"
        )

    def test_get_approved(self):
        """Manager should return all approved agencies"""
        agencies = Agency.objects.get_approved()
        ok_(self.agency1 in agencies)
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies)

    def test_get_siblings(self):
        """Manager should return all siblings to a given agency"""
        agencies = Agency.objects.get_siblings(self.agency1)
        ok_(
            self.agency1 not in agencies,
            "The given agency shouldn't be its own sibling.",
        )
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies, "Unapproved agencies shouldn't be siblings.")


class TestAgencyViews(TestCase):
    """Tests for Agency views"""

    def setUp(self):
        self.agency = AgencyFactory()
        self.url = self.agency.get_absolute_url()
        self.view = detail
        self.user = UserFactory()
        self.kwargs = {
            "jurisdiction": self.agency.jurisdiction.slug,
            "jidx": self.agency.jurisdiction.id,
            "slug": self.agency.slug,
            "idx": self.agency.id,
        }

    def test_approved_ok(self):
        """An approved agency should return an 200 response."""
        response = http_get_response(self.url, self.view, self.user, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_unapproved_not_found(self):
        """An unapproved agency should return a 404 response."""
        self.agency.status = "pending"
        self.agency.save()
        http_get_response(self.url, self.view, self.user, **self.kwargs)

    def test_list(self):
        """The list should only contain approved agencies"""
        approved_agency = AgencyFactory()
        unapproved_agency = AgencyFactory(status="pending")
        response = http_get_response(reverse("agency-list"), AgencyList.as_view())
        agency_list = response.context_data["object_list"]
        ok_(approved_agency in agency_list, "Approved agencies should be listed.")
        ok_(
            unapproved_agency not in agency_list,
            "Unapproved agencies should not be listed.",
        )

    def test_boilerplate(self):
        """Test the boilerplate ajax view"""
        agencies = AgencyFactory.create_batch(2)
        request = RequestFactory().get(
            reverse("agency-boilerplate"), {"agencies": [a.pk for a in agencies]}
        )
        request = mock_middleware(request)
        request.user = UserFactory(profile__full_name="John Doe")
        response = boilerplate(request)
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        assert_in("{ law name }", data["intro"])
        assert_in("{ days }", data["outro"])
        assert_in("John Doe", data["outro"])

    def test_contact_info_anonymous(self):
        """Test the contact_info ajax view"""
        agency = AgencyFactory()

        request = RequestFactory().get(
            reverse("agency-contact-info", kwargs={"idx": agency.pk})
        )
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = contact_info(request, agency.pk)
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data["type"], "email")

    def test_contact_info(self):
        """Test the contact_info ajax view"""
        agency = AgencyFactory()

        request = RequestFactory().get(
            reverse("agency-contact-info", kwargs={"idx": agency.pk})
        )
        request = mock_middleware(request)
        request.user = ProfessionalUserFactory()
        response = contact_info(request, agency.pk)
        eq_(response.status_code, 200)
        data = json.loads(response.content)
        eq_(data["email"], str(agency.email))


class TestAgencyForm(TestCase):
    """Tests the AgencyForm"""

    def setUp(self):
        self.agency = AgencyFactory()
        self.form = AgencyForm(
            {
                "name": self.agency.name,
                "jurisdiction": self.agency.jurisdiction.pk,
                "portal_type": "other",
            },
            instance=self.agency,
        )

    def test_validate_empty_form(self):
        """The form should have a name, at least"""
        ok_(not AgencyForm().is_valid(), "Empty AgencyForm should not validate.")

    def test_instance_form(self):
        """The form should validate given only instance data"""
        ok_(self.form.is_valid())
