"""
Tests for guarding agency user accounts
"""

# Django
from django.test import TestCase
from django.urls import reverse

# Standard Library
from unittest.mock import patch
from urllib.parse import urlsplit

# MuckRock
from muckrock.accounts.forms import BuyRequestForm
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.constants import AGENCY_USER_MESSAGE
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.forms.detail import RequestFeeForm


class TestAgencyUserLoginLog(TestCase):
    """Agency user logins are logged"""

    logger_name = "muckrock.accounts.signals"

    def test_agency_reply_link_login_is_logged(self):
        """Following the login link from an agency email logs who and where"""
        agency = AgencyFactory()
        agency_user = agency.profile.user
        foia = FOIARequestFactory(agency=agency)
        link = urlsplit(foia.get_agency_reply_link())

        with self.assertLogs(self.logger_name, "INFO") as logs:
            self.client.get(
                f"{link.path}?{link.query}",
                HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1",
                HTTP_USER_AGENT="Test Browser",
            )

        assert len(logs.output) == 1
        output = logs.output[0]
        assert "Agency user login" in output
        assert f"user={agency_user.username} ({agency_user.pk})" in output
        assert f"agency={agency.name} ({agency.pk})" in output
        assert "forwarded_for=203.0.113.7, 10.0.0.1 " in output
        assert "user_agent=Test Browser" in output

    def test_regular_user_login_is_not_logged(self):
        """Ordinary logins do not add to the agency login log"""
        with self.assertNoLogs(self.logger_name, "INFO"):
            self.client.force_login(UserFactory())


class TestAgencyUserFiling(TestCase):
    """Agency users may not file requests"""

    def test_agency_user_may_not_file(self):
        """An agency user lacks the add permission and is told why"""
        user = AgencyFactory().profile.user
        assert not user.has_perm("foia.add_foiarequest")
        assert user.profile.filing_blocked_message == AGENCY_USER_MESSAGE

    def test_regular_user_may_file(self):
        """Ordinary users are not blocked"""
        user = UserFactory()
        assert user.has_perm("foia.add_foiarequest")
        assert user.profile.filing_blocked_message is None


class TestAgencyUserPayments(TestCase):
    """Agency users may not pay for requests or fees"""

    def _form(self, form_class, user, **data):
        """A payment form with a new card, otherwise valid"""
        return form_class(
            {"stripe_token": "tok_test", "stripe_pk": "pk_test", **data},
            user=user,
            organization=user.profile.individual_organization,
        )

    def test_buy_requests_form(self):
        """An agency user may not buy requests"""
        regular = self._form(BuyRequestForm, UserFactory(), num_requests=5)
        assert regular.is_valid(), regular.errors

        agency = self._form(
            BuyRequestForm, AgencyFactory().profile.user, num_requests=5
        )
        assert not agency.is_valid()
        assert AGENCY_USER_MESSAGE in agency.non_field_errors()

    def test_request_fee_form(self):
        """An agency user may not pay request fees"""
        regular = self._form(RequestFeeForm, UserFactory(), amount=100)
        assert regular.is_valid(), regular.errors

        agency = self._form(RequestFeeForm, AgencyFactory().profile.user, amount=100)
        assert not agency.is_valid()
        assert AGENCY_USER_MESSAGE in agency.non_field_errors()

    def test_profile_hides_buy_form(self):
        """An agency user's profile page offers no way to buy requests"""
        regular = UserFactory()
        self.client.force_login(regular)
        response = self.client.get(
            reverse("acct-profile", kwargs={"username": regular.username})
        )
        assert b'id="buy-requests"' in response.content

        agency_user = AgencyFactory().profile.user
        self.client.force_login(agency_user)
        response = self.client.get(
            reverse("acct-profile", kwargs={"username": agency_user.username})
        )
        assert response.status_code == 200
        assert b'id="buy-requests"' not in response.content

    def _post_buy(self, user):
        """Post a valid request purchase from the user's own profile page"""
        user.memberships.update(admin=True)
        self.client.force_login(user)
        self.client.post(
            reverse("acct-profile", kwargs={"username": user.username}),
            {
                "stripe_token": "tok_test",
                "stripe_pk": "pk_test",
                "num_requests": 5,
                "organization": user.profile.individual_organization.pk,
                "use_card_on_file": "False",
            },
        )

    @patch("muckrock.organization.models.Organization.pay")
    def test_profile_buy_post(self, mock_pay):
        """Posting to buy requests as an agency user charges nothing"""
        self._post_buy(UserFactory())
        mock_pay.assert_called_once()
        mock_pay.reset_mock()

        self._post_buy(AgencyFactory().profile.user)
        mock_pay.assert_not_called()
