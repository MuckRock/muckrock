"""Tests for the HIDE_FILES_FROM_SCRAPERS killswitch"""

# Django
from django.test import TestCase, override_settings
from django.urls import reverse

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIAFileFactory

LOCMEM_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "lock": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


class HideFilesTestCase(TestCase):
    """Shared setup for killswitch tests"""

    def setUp(self):
        self.file = FOIAFileFactory(comm__foia__embargo_status="public")
        self.foia = self.file.comm.foia
        self.agency = self.foia.agency
        self.user = UserFactory()

    def foia_files_url(self):
        """URL for the FOIA request file list"""
        return reverse(
            "foia-files",
            kwargs={
                "jurisdiction": self.foia.jurisdiction.slug,
                "jidx": self.foia.jurisdiction.pk,
                "slug": self.foia.slug,
                "idx": self.foia.pk,
            },
        )

    def agency_files_url(self):
        """URL for the agency file list"""
        return reverse(
            "agency-files",
            kwargs={
                "jurisdiction": self.agency.jurisdiction.slug,
                "jidx": self.agency.jurisdiction.pk,
                "slug": self.agency.slug,
                "idx": self.agency.pk,
            },
        )

    def embed_url(self):
        """URL for the file embed"""
        return reverse("file-embed", kwargs={"pk": self.file.pk})


@override_settings(HIDE_FILES_FROM_SCRAPERS=True)
class KillswitchOnTests(HideFilesTestCase):
    """Anonymous users cannot see files; logged-in users can"""

    def test_foia_file_list_redirects_anonymous(self):
        """Anonymous users are redirected to login from the FOIA file list"""
        response = self.client.get(self.foia_files_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("acct-login"), response.url)

    def test_agency_file_list_redirects_anonymous(self):
        """Anonymous users are redirected to login from the agency file list"""
        response = self.client.get(self.agency_files_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("acct-login"), response.url)

    def test_embed_shows_login_prompt_to_anonymous(self):
        """Anonymous users get the login prompt instead of the embed"""
        response = self.client.get(self.embed_url())
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "foia/file/embed_login.html")
        self.assertNotContains(response, "viewer-iframe", status_code=403)

    def test_foia_detail_hides_files_from_anonymous(self):
        """Anonymous users see a login prompt instead of request files"""
        response = self.client.get(self.foia.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "to view files for this request")
        self.assertNotContains(response, 'id="all-files"')

    def test_agency_detail_hides_files_from_anonymous(self):
        """Anonymous users see a login prompt instead of agency files"""
        response = self.client.get(self.agency.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "to view files from this agency")
        self.assertNotContains(response, 'id="all-files"')

    def test_logged_in_user_sees_foia_file_list(self):
        """Logged-in users can view the FOIA file list"""
        self.client.force_login(self.user)
        response = self.client.get(self.foia_files_url())
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_sees_agency_file_list(self):
        """Logged-in users can view the agency file list"""
        self.client.force_login(self.user)
        response = self.client.get(self.agency_files_url())
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_sees_embed(self):
        """Logged-in users can view the file embed"""
        self.client.force_login(self.user)
        response = self.client.get(self.embed_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "foia/file/embed.html")


@override_settings(HIDE_FILES_FROM_SCRAPERS=False)
class KillswitchOffTests(HideFilesTestCase):
    """Everything behaves as before for anonymous users"""

    def test_foia_file_list_visible(self):
        """Anonymous users can view the FOIA file list"""
        response = self.client.get(self.foia_files_url())
        self.assertEqual(response.status_code, 200)

    def test_agency_file_list_visible(self):
        """Anonymous users can view the agency file list"""
        response = self.client.get(self.agency_files_url())
        self.assertEqual(response.status_code, 200)

    def test_embed_visible(self):
        """Anonymous users can view the file embed"""
        response = self.client.get(self.embed_url())
        self.assertEqual(response.status_code, 200)

    def test_foia_detail_shows_files(self):
        """Anonymous users see request files with no login prompt"""
        response = self.client.get(self.foia.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "to view files for this request")


@override_settings(CACHES=LOCMEM_CACHES)
class KillswitchCacheTests(HideFilesTestCase):
    """Flipping the killswitch takes effect despite the detail fragment cache"""

    def test_toggle_is_not_served_from_stale_cache(self):
        """Turning the killswitch off is not masked by a cached render"""
        url = self.foia.get_absolute_url()
        with self.settings(HIDE_FILES_FROM_SCRAPERS=True):
            response = self.client.get(url)
            self.assertContains(response, "to view files for this request")
        with self.settings(HIDE_FILES_FROM_SCRAPERS=False):
            response = self.client.get(url)
            self.assertNotContains(response, "to view files for this request")
