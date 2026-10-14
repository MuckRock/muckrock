"""
Tests for FOIA request filters
"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.utils import timezone

# Standard Library
from datetime import datetime

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import assert_page_queries_do_not_scale
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAFileFactory,
    FOIARequestFactory,
)
from muckrock.foia.filters import FOIARequestFilterSet
from muckrock.foia.models import FOIARequest


def aware(year, month, day):
    """Return a timezone aware datetime at midnight"""
    return timezone.make_aware(datetime(year, month, day))


class CommunicationDateRangeFilterTests(TestCase):
    """Tests for filter_communication_date_range"""

    def setUp(self):
        self.filterset = FOIARequestFilterSet()
        self.early = FOIARequestFactory()
        self.late = FOIARequestFactory()
        self.no_comms = FOIARequestFactory()
        FOIACommunicationFactory(foia=self.early, datetime=aware(2025, 1, 15))
        FOIACommunicationFactory(foia=self.late, datetime=aware(2025, 6, 15))
        self.foias = FOIARequest.objects.filter(
            pk__in=[self.early.pk, self.late.pk, self.no_comms.pk]
        )

    def filter(self, start, stop):
        """Run the date range filter over the test requests"""
        return self.filterset.filter_communication_date_range(
            self.foias, "date_range", slice(start, stop)
        )

    def test_start_and_stop(self):
        """Both bounds keep only requests with a communication inside the range"""
        results = self.filter(aware(2025, 1, 1), aware(2025, 2, 1))
        self.assertEqual(set(results), {self.early})

    def test_start_only(self):
        """A start date alone keeps requests with a communication on or after it"""
        results = self.filter(aware(2025, 6, 1), None)
        self.assertEqual(set(results), {self.late})

    def test_stop_only(self):
        """A stop date alone keeps requests with a communication on or before it"""
        results = self.filter(None, aware(2025, 2, 1))
        self.assertEqual(set(results), {self.early})

    def test_no_duplicates(self):
        """A request with several matching communications appears once"""
        FOIACommunicationFactory(foia=self.early, datetime=aware(2025, 1, 20))
        results = self.filter(aware(2025, 1, 1), aware(2025, 2, 1))
        self.assertEqual(results.count(), 1)


class MinimumPagesFilterTests(TestCase):
    """Tests for filter_minimum_pages"""

    def setUp(self):
        self.filterset = FOIARequestFilterSet()
        self.small = FOIARequestFactory()
        self.large = FOIARequestFactory()
        self.no_files = FOIARequestFactory()
        FOIAFileFactory(comm=FOIACommunicationFactory(foia=self.small), pages=3)
        FOIAFileFactory(comm=FOIACommunicationFactory(foia=self.large), pages=12)
        FOIAFileFactory(comm=FOIACommunicationFactory(foia=self.large), pages=40)
        self.foias = FOIARequest.objects.filter(
            pk__in=[self.small.pk, self.large.pk, self.no_files.pk]
        )

    def filter(self, value):
        """Run the minimum pages filter over the test requests"""
        return self.filterset.filter_minimum_pages(self.foias, "minimum_pages", value)

    def test_zero_skips_filter(self):
        """0 returns every request, including ones with no files"""
        results = self.filter(0)
        self.assertEqual(set(results), {self.small, self.large, self.no_files})

    def test_minimum(self):
        """Only requests with a file at or above the minimum are kept"""
        self.assertEqual(set(self.filter(10)), {self.large})

    def test_boundary(self):
        """A file with exactly the minimum number of pages matches"""
        self.assertEqual(set(self.filter(3)), {self.small, self.large})

    def test_no_duplicates(self):
        """A request with several matching files appears once"""
        self.assertEqual(self.filter(10).count(), 1)


class FileTypesFilterTests(TestCase):
    """Tests for filter_file_types"""

    def setUp(self):
        self.filterset = FOIARequestFilterSet()
        self.pdf = FOIARequestFactory()
        self.csv = FOIARequestFactory()
        self.archive = FOIARequestFactory()
        self.lookalike = FOIARequestFactory()
        self.no_files = FOIARequestFactory()
        FOIAFileFactory(
            comm=FOIACommunicationFactory(foia=self.pdf), ffile__filename="report.PDF"
        )
        FOIAFileFactory(
            comm=FOIACommunicationFactory(foia=self.pdf), ffile__filename="memo.pdf"
        )
        FOIAFileFactory(
            comm=FOIACommunicationFactory(foia=self.csv), ffile__filename="data.csv"
        )
        FOIAFileFactory(
            comm=FOIACommunicationFactory(foia=self.archive),
            ffile__filename="records.tar.gz",
        )
        FOIAFileFactory(
            comm=FOIACommunicationFactory(foia=self.lookalike),
            ffile__filename="scanpdf",
        )
        self.foias = FOIARequest.objects.filter(
            pk__in=[
                self.pdf.pk,
                self.csv.pk,
                self.archive.pk,
                self.lookalike.pk,
                self.no_files.pk,
            ]
        )

    def filter(self, value):
        """Run the file types filter over the test requests"""
        return self.filterset.filter_file_types(self.foias, "file_types", value)

    def test_case_insensitive(self):
        """Lowercase input matches an uppercase extension"""
        self.assertEqual(set(self.filter("pdf")), {self.pdf})

    def test_leading_dot_optional(self):
        """A leading dot in the input gives the same result as none"""
        self.assertEqual(set(self.filter(".pdf")), set(self.filter("pdf")))

    def test_extension_only(self):
        """A name ending in the letters without a dot does not match"""
        self.assertNotIn(self.lookalike, set(self.filter("pdf")))

    def test_compound_extension(self):
        """A two part extension matches in full or by its last part"""
        self.assertEqual(set(self.filter("tar.gz")), {self.archive})
        self.assertEqual(set(self.filter("gz")), {self.archive})

    def test_multiple_types(self):
        """Comma separated types match any of them, ignoring spaces and case"""
        self.assertEqual(set(self.filter("pdf, CSV")), {self.pdf, self.csv})

    def test_blank_entries_ignored(self):
        """Blank entries are skipped instead of matching every file"""
        self.assertEqual(set(self.filter("pdf, ,")), {self.pdf})

    def test_only_blank_skips_filter(self):
        """Input with no usable types returns every request"""
        results = self.filter(" , ")
        self.assertEqual(
            set(results),
            {self.pdf, self.csv, self.archive, self.lookalike, self.no_files},
        )

    def test_no_duplicates(self):
        """A request with several matching files appears once"""
        self.assertEqual(self.filter("pdf").count(), 1)


class FilterQueryScalingTests(TestCase):
    """The filtered request list stays flat in queries and rows as files grow"""

    def create_one(self):
        """Create a public done request with two communications of two files each"""
        foia = FOIARequestFactory(status="done", embargo_status="public")
        for _ in range(2):
            comm = FOIACommunicationFactory(foia=foia, datetime=aware(2025, 1, 15))
            FOIAFileFactory(comm=comm, pages=12, ffile__filename="report.pdf")
            FOIAFileFactory(comm=comm, pages=12, ffile__filename="data.csv")

    def test_date_range(self):
        """The date range filter does not multiply rows by communications"""
        url = "/foi/list/?date_range_min=01/01/2025&date_range_max=02/01/2025"
        assert_page_queries_do_not_scale(self.client, url, self.create_one)

    def test_minimum_pages(self):
        """The minimum pages filter does not multiply rows by files"""
        url = "/foi/list/?minimum_pages=10"
        assert_page_queries_do_not_scale(self.client, url, self.create_one)

    def test_file_types(self):
        """The file types filter does not multiply rows by files or types"""
        url = "/foi/list/?file_types=pdf,%20csv"
        assert_page_queries_do_not_scale(self.client, url, self.create_one)


class HasFilesFilterTests(TestCase):
    """Tests for filter_has_files"""

    def setUp(self):
        self.filterset = FOIARequestFilterSet()
        self.with_files = FOIARequestFactory()
        self.no_files = FOIARequestFactory()
        self.comm_only = FOIARequestFactory()
        comm = FOIACommunicationFactory(foia=self.with_files)
        FOIAFileFactory(comm=comm)
        FOIAFileFactory(comm=comm)
        FOIACommunicationFactory(foia=self.comm_only)
        self.foias = FOIARequest.objects.filter(
            pk__in=[self.with_files.pk, self.no_files.pk, self.comm_only.pk]
        )

    def filterset_for(self, user):
        """Build the filterset for a request made by the given user"""
        request = RequestFactory().get("/foi/list/")
        request.user = user
        return FOIARequestFilterSet(request.GET, queryset=self.foias, request=request)

    def test_has_files(self):
        """True keeps only requests with at least one file, once each"""
        results = self.filterset.filter_has_files(self.foias, "has_files", True)
        self.assertEqual(list(results), [self.with_files])

    def test_has_no_files(self):
        """False keeps requests with no files, with or without communications"""
        results = self.filterset.filter_has_files(self.foias, "has_files", False)
        self.assertEqual(set(results), {self.no_files, self.comm_only})

    def test_logged_in_users_get_filter(self):
        """Logged in users see the has files filter"""
        self.assertIn("has_files", self.filterset_for(UserFactory()).filters)

    def test_anonymous_users_do_not_get_filter(self):
        """Logged out users do not see or use the has files filter"""
        self.assertNotIn("has_files", self.filterset_for(AnonymousUser()).filters)
