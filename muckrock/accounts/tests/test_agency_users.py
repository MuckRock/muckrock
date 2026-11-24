"""
Tests for guarding agency user accounts
"""

# Django
from django.test import TestCase

# Standard Library
from urllib.parse import urlsplit

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import FOIARequestFactory


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
