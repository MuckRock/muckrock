"""
Tests for the FOIA views
"""

# pylint: disable=invalid-name
# pylint: disable=too-many-lines

# Django
from django.contrib.auth.models import AnonymousUser, User
from django.http.request import QueryDict
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

# Standard Library
import datetime
from datetime import date, timedelta
from operator import attrgetter

# Third Party
import nose.tools
import requests_mock
from actstream.actions import follow, is_following, unfollow
from nose.tools import (
    assert_false,
    assert_in,
    assert_is_none,
    assert_not_in,
    assert_true,
    eq_,
    ok_,
    raises,
)

# MuckRock
from muckrock.core.factories import (
    AgencyFactory,
    AppealAgencyFactory,
    OrganizationUserFactory,
    ProfessionalUserFactory,
    ProjectFactory,
    UserFactory,
)
from muckrock.core.test_utils import http_post_response, mock_middleware, mock_squarelet
from muckrock.core.tests import get_404, get_allowed
from muckrock.crowdfund.models import Crowdfund
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAComposerFactory,
    FOIARequestFactory,
    FOIATemplateFactory,
)
from muckrock.foia.models import FOIAComposer, FOIARequest
from muckrock.foia.views import (
    ComposerDetail,
    CreateComposer,
    Detail,
    FollowingRequestList,
    MyRequestList,
    RequestList,
    UpdateComposer,
    autosave,
    crowdfund_request,
    raw,
)
from muckrock.jurisdiction.factories import ExampleAppealFactory
from muckrock.jurisdiction.models import Appeal
from muckrock.project.forms import ProjectManagerForm
from muckrock.task.factories import ResponseTaskFactory
from muckrock.task.models import StatusChangeTask


class TestFOIAViews(TestCase):
    """Functional tests for FOIA"""

    def setUp(self):
        """Set up tests"""
        UserFactory(username="MuckrockStaff")

    # views
    def test_foia_list(self):
        """Test the foia-list view"""

        response = get_allowed(self.client, reverse("foia-list"))
        nose.tools.eq_(
            set(response.context["object_list"]),
            set(
                FOIARequest.objects.get_viewable(AnonymousUser()).order_by(
                    "-composer__datetime_submitted"
                )[:12]
            ),
        )

    def test_foia_list_user(self):
        """Test the foia-list-user view"""

        users = UserFactory.create_batch(2)
        FOIARequestFactory.create_batch(4, composer__user=users[0])
        FOIARequestFactory.create_batch(3, composer__user=users[1])

        for user in users:
            response = get_allowed(
                self.client, reverse("foia-list-user", kwargs={"user_pk": user.pk})
            )
            nose.tools.eq_(
                set(response.context["object_list"]),
                set(
                    FOIARequest.objects.get_viewable(AnonymousUser()).filter(
                        composer__user=user
                    )
                ),
            )
            nose.tools.ok_(
                all(foia.user == user for foia in response.context["object_list"])
            )

    def test_foia_sorted_list(self):
        """Test sorting on foia-list view"""

        for field in ["title", "date_submitted"]:
            for order in ["asc", "desc"]:
                response = get_allowed(
                    self.client,
                    reverse("foia-list") + "?sort=%s&order=%s" % (field, order),
                )
                nose.tools.eq_(
                    [f.title for f in response.context["object_list"]],
                    [
                        f.title
                        for f in sorted(
                            response.context["object_list"],
                            key=attrgetter(field),
                            reverse=(order == "desc"),
                        )
                    ],
                )

    def test_foia_bad_sort(self):
        """Test sorting against a non-existant field"""
        response = get_allowed(self.client, reverse("foia-list") + "?sort=test")
        nose.tools.eq_(response.status_code, 200)

    def test_foia_detail(self):
        """Test the foia-detail view"""

        foia = FOIARequestFactory()
        get_allowed(
            self.client,
            reverse(
                "foia-detail",
                kwargs={
                    "idx": foia.pk,
                    "slug": foia.slug,
                    "jurisdiction": foia.jurisdiction.slug,
                    "jidx": foia.jurisdiction.pk,
                },
            ),
        )

    def test_feeds(self):
        """Test the RSS feed views"""

        user = UserFactory()
        foias = FOIARequestFactory.create_batch(4, composer__user=user)

        get_allowed(self.client, reverse("foia-submitted-feed"))
        get_allowed(self.client, reverse("foia-done-feed"))
        get_allowed(self.client, reverse("foia-feed", kwargs={"idx": foias[0].pk}))
        get_allowed(
            self.client,
            reverse("foia-user-submitted-feed", kwargs={"username": user.username}),
        )
        get_allowed(
            self.client,
            reverse("foia-user-done-feed", kwargs={"username": user.username}),
        )
        get_allowed(
            self.client, reverse("foia-user-feed", kwargs={"username": user.username})
        )

    def test_404_views(self):
        """Test views that should give a 404 error"""

        get_404(
            self.client,
            reverse(
                "foia-detail",
                kwargs={
                    "idx": 1,
                    "slug": "test-c",
                    "jurisdiction": "massachusetts",
                    "jidx": 1,
                },
            ),
        )
        get_404(
            self.client,
            reverse(
                "foia-detail",
                kwargs={
                    "idx": 2,
                    "slug": "test-c",
                    "jurisdiction": "massachusetts",
                    "jidx": 1,
                },
            ),
        )


class TestRequestDetailView(TestCase):
    """Request detail views support a wide variety of interactions"""

    def setUp(self):
        agency = AgencyFactory(appeal_agency=AppealAgencyFactory())
        self.foia = FOIARequestFactory(agency=agency)
        self.view = Detail.as_view()
        self.url = self.foia.get_absolute_url()
        self.kwargs = {
            "jurisdiction": self.foia.jurisdiction.slug,
            "jidx": self.foia.jurisdiction.id,
            "slug": self.foia.slug,
            "idx": self.foia.id,
        }
        UserFactory(username="MuckrockStaff")

    def test_add_tags(self):
        """Posting a collection of tags to a request should update its tags."""
        data = {"action": "tags", "tags": ["foo", "bar"]}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        ok_("foo" in [tag.name for tag in self.foia.tags.all()])
        ok_("bar" in [tag.name for tag in self.foia.tags.all()])

    def test_add_projects(self):
        """Posting a collection of projects to a request should add it to those projects."""
        project = ProjectFactory()
        project.contributors.add(self.foia.user)
        form = ProjectManagerForm({"projects": [project.pk]}, user=self.foia.user)
        ok_(form.is_valid())
        data = {"action": "projects"}
        data.update(form.data)
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        project.refresh_from_db()
        ok_(self.foia in project.requests.all())

    def test_appeal(self):
        """Appealing a request should send a new communication,
        record the details of the appeal, and update the status of the request."""
        comm_count = self.foia.communications.count()
        data = {"action": "appeal", "text": "Lorem ipsum"}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, "appealing")
        eq_(self.foia.communications.count(), comm_count + 1)
        eq_(
            self.foia.communications.last().communication,
            data["text"],
            "The appeal should use the language provided by the user.",
        )
        appeal = Appeal.objects.last()
        ok_(appeal, "An Appeal object should be created.")
        eq_(
            self.foia.communications.last(),
            appeal.communication,
            "The appeal should reference the communication that was created.",
        )

    def test_appeal_example(self):
        """If an example appeal is used to base the appeal off of,
        then the examples should be recorded to the appeal object as well."""
        example_appeal = ExampleAppealFactory()
        data = {
            "action": "appeal",
            "text": "Lorem ipsum",
            "base_language": example_appeal.pk,
        }
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        appeal = Appeal.objects.last()
        ok_(appeal.base_language, "The appeal should record its base language.")
        ok_(appeal.base_language.count(), 1)

    def test_unauthorized_appeal(self):
        """Appealing a request without permission should not do anything."""
        unauth_user = UserFactory()
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {"action": "appeal", "text": "Lorem ipsum"}
        http_post_response(self.url, self.view, data, unauth_user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(
            self.foia.status,
            previous_status,
            "The status of the request should not be changed.",
        )
        eq_(
            self.foia.communications.count(),
            comm_count,
            "No communication should be added to the request.",
        )

    def test_missing_appeal(self):
        """An appeal that is missing its language should not do anything."""
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {"action": "appeal", "text": ""}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(
            self.foia.status,
            previous_status,
            "The status of the request should not be changed.",
        )
        eq_(
            self.foia.communications.count(),
            comm_count,
            "No communication should be added to the request.",
        )

    def test_unappealable_request(self):
        """An appeal on a request that cannot be appealed should not do anything."""
        self.foia.status = "submitted"
        self.foia.save()
        nose.tools.assert_false(self.foia.has_perm(self.foia.user, "appeal"))
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {"action": "appeal", "text": "Lorem ipsum"}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(
            self.foia.status,
            previous_status,
            "The status of the request should not be changed.",
        )
        eq_(
            self.foia.communications.count(),
            comm_count,
            "No communication should be added to the request.",
        )

    def test_post_status(self):
        """A user updating the status of their request should update the status,
        open a status change task, and close any open response tasks"""
        nose.tools.assert_not_equal(self.foia.status, "done")
        eq_(
            len(
                StatusChangeTask.objects.filter(
                    foia=self.foia, user=self.foia.user, resolved=False
                )
            ),
            0,
        )
        communication = FOIACommunicationFactory(foia=self.foia)
        response_task = ResponseTaskFactory(communication=communication, resolved=False)
        data = {"action": "status", "status": "done"}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, "done")
        eq_(
            len(
                StatusChangeTask.objects.filter(
                    foia=self.foia, user=self.foia.user, resolved=False
                )
            ),
            1,
        )
        response_task.refresh_from_db()
        ok_(response_task.resolved)


class TestFollowingRequestList(TestCase):
    """Test to make sure following request list shows correct requests"""

    def test_following_request_list(self):
        """Test to make sure following request list shows correct requests"""
        user = UserFactory()
        factory = RequestFactory()
        request = factory.get(reverse("foia-list-following"))
        request.user = user
        foias = FOIARequestFactory.create_batch(7)
        for foia in foias[::2]:
            follow(user, foia)
        response = FollowingRequestList.as_view()(request)
        eq_(len(response.context_data["object_list"]), 4)
        for foia in foias[::2]:
            nose.tools.assert_in(foia, response.context_data["object_list"])

        unfollow(user, foias[2])
        response = FollowingRequestList.as_view()(request)
        eq_(len(response.context_data["object_list"]), 3)
        for foia in (foias[0], foias[4], foias[6]):
            nose.tools.assert_in(foia, response.context_data["object_list"])


class TestBulkActions(TestCase):
    """Test the bulk actions on the list views"""

    # pylint: disable=protected-access

    def test_follow(self):
        """Test bulk following"""
        public_foia = FOIARequestFactory()
        private_foia = FOIARequestFactory(embargo=True)
        user = UserFactory()

        RequestList()._follow(
            FOIARequest.objects.filter(pk__in=[public_foia.pk, private_foia.pk]),
            user,
            {},
        )

        ok_(is_following(user, public_foia))
        assert_false(is_following(user, private_foia))

    def test_unfollow(self):
        """Test bulk unfollowing"""
        follow_foia = FOIARequestFactory()
        unfollow_foia = FOIARequestFactory()
        user = UserFactory()

        follow(user, follow_foia, actor_only=False)

        RequestList()._unfollow(
            FOIARequest.objects.filter(pk__in=[follow_foia.pk, unfollow_foia.pk]),
            user,
            {},
        )

        assert_false(is_following(user, follow_foia))
        assert_false(is_following(user, unfollow_foia))

    def test_extend_embargo(self):
        """Test bulk embargo extending"""
        tomorrow = date.today() + timedelta(1)
        next_month = date.today() + timedelta(30)
        user = ProfessionalUserFactory()
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(
            composer__user=user, embargo=False, status="ack"
        )
        embargo_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="ack"
        )
        embargo_done_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="done", date_embargo=tomorrow
        )

        MyRequestList()._extend_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        ok_(public_foia.embargo)
        assert_is_none(public_foia.date_embargo)
        ok_(embargo_foia.embargo)
        assert_is_none(embargo_foia.date_embargo)
        ok_(embargo_done_foia.embargo)
        eq_(embargo_done_foia.date_embargo, next_month)

    def test_remove_embargo(self):
        """Test bulk embargo removing"""
        tomorrow = date.today() + timedelta(1)
        user = ProfessionalUserFactory()
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(
            composer__user=user, embargo=False, status="ack"
        )
        embargo_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="ack"
        )
        embargo_done_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="done", date_embargo=tomorrow
        )

        MyRequestList()._remove_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        assert_false(public_foia.embargo)
        assert_false(embargo_foia.embargo)
        assert_false(embargo_done_foia.embargo)

    def test_perm_embargo(self):
        """Test bulk permanent embargo"""
        tomorrow = date.today() + timedelta(1)
        user = OrganizationUserFactory()
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(
            composer__user=user, embargo=False, status="ack"
        )
        embargo_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="ack"
        )
        embargo_done_foia = FOIARequestFactory(
            composer__user=user, embargo=True, status="done", date_embargo=tomorrow
        )

        MyRequestList()._perm_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        ok_(public_foia.embargo)
        assert_false(public_foia.permanent_embargo)
        ok_(embargo_foia.embargo)
        assert_false(embargo_foia.permanent_embargo)
        ok_(embargo_done_foia.embargo)
        ok_(embargo_done_foia.permanent_embargo)

    def test_projects(self):
        """Test bulk add to projects"""
        user = UserFactory()
        foia = FOIARequestFactory(composer__user=user)
        proj = ProjectFactory()
        proj.contributors.add(user)

        MyRequestList()._project(
            FOIARequest.objects.filter(pk=foia.pk), user, {"projects": [proj.pk]}
        )

        foia.refresh_from_db()

        assert_in(proj, foia.projects.all())

    def test_tags(self):
        """Test bulk add tags"""
        user = UserFactory()
        foia = FOIARequestFactory(composer__user=user)

        MyRequestList()._tags(
            FOIARequest.objects.filter(pk=foia.pk),
            user,
            QueryDict("tags=red&tags=blue"),
        )

        foia.refresh_from_db()

        tags = [t.name for t in foia.tags.all()]

        assert_in("red", tags)
        assert_in("blue", tags)

    def test_share(self):
        """Test bulk sharing"""
        user = UserFactory()
        share_user = UserFactory()
        foia = FOIARequestFactory(composer__user=user)

        MyRequestList()._share(
            FOIARequest.objects.filter(pk=foia.pk),
            user,
            {"access": "edit", "users": [share_user.pk]},
        )

        foia.refresh_from_db()

        assert_in(share_user, foia.edit_collaborators.all())
        assert_not_in(share_user, foia.read_collaborators.all())

    def test_autofollowup_on(self):
        """Test bulk autofollowup enabling"""
        user = UserFactory()
        on_foia = FOIARequestFactory(composer__user=user, disable_autofollowups=False)
        off_foia = FOIARequestFactory(composer__user=user, disable_autofollowups=True)

        MyRequestList()._autofollowup_on(
            FOIARequest.objects.filter(pk__in=[on_foia.pk, off_foia.pk]), user, {}
        )

        on_foia.refresh_from_db()
        off_foia.refresh_from_db()

        assert_false(on_foia.disable_autofollowups)
        assert_false(off_foia.disable_autofollowups)

    def test_autofollowup_off(self):
        """Test bulk autofollowup disabling"""
        user = UserFactory()
        on_foia = FOIARequestFactory(composer__user=user, disable_autofollowups=False)
        off_foia = FOIARequestFactory(composer__user=user, disable_autofollowups=True)

        MyRequestList()._autofollowup_off(
            FOIARequest.objects.filter(pk__in=[on_foia.pk, off_foia.pk]), user, {}
        )

        on_foia.refresh_from_db()
        off_foia.refresh_from_db()

        ok_(on_foia.disable_autofollowups)
        ok_(off_foia.disable_autofollowups)


class TestRawEmail(TestCase):
    """Tests the raw email view"""

    def setUp(self):
        """Set up for tests"""
        self.comm = FOIACommunicationFactory(
            foia__composer__user=ProfessionalUserFactory()
        )
        self.request_factory = RequestFactory()
        self.url = reverse("foia-raw", kwargs={"idx": self.comm.id})
        self.view = raw

    def test_raw_email_view(self):
        """Advanced users should be able to view raw emails"""
        free_user = UserFactory()
        pro_user = self.comm.foia.user
        request = self.request_factory.get(self.url)
        request.user = free_user
        response = self.view(request, self.comm.id)
        eq_(response.status_code, 302, "Free users should be denied access.")
        request.user = pro_user
        response = self.view(request, self.comm.id)
        eq_(response.status_code, 200, "Advanced users should be allowed access.")


class TestFOIACrowdfunding(TestCase):
    """Tests for FOIA Crowdfunding"""

    def setUp(self):
        self.foia = FOIARequestFactory(status="payment")
        self.url = reverse(
            "foia-crowdfund",
            args=(
                self.foia.jurisdiction.slug,
                self.foia.jurisdiction.id,
                self.foia.slug,
                self.foia.id,
            ),
        )
        self.request_factory = RequestFactory()
        self.view = crowdfund_request

    def get_res(self, user):
        """Returns a GET response from the endpoint."""
        if user is None:
            user = AnonymousUser()
        request = self.request_factory.get(self.url)
        request.user = user
        request = mock_middleware(request)
        return self.view(request, self.foia.pk)

    def post_res(self, user, data):
        """Returns a POST response from the endpoint."""
        if user is None:
            user = AnonymousUser()
        request = self.request_factory.post(self.url, data)
        request.user = user
        request = mock_middleware(request)
        return self.view(request, self.foia.pk)

    def test_crowdfund_url(self):
        """Crowdfund creation should use the /crowdfund endpoint of a request."""
        expected_url = (
            "/foi/"
            + self.foia.jurisdiction.slug
            + "-"
            + str(self.foia.jurisdiction.id)
            + "/"
            + self.foia.slug
            + "-"
            + str(self.foia.id)
            + "/crowdfund/"
        )
        nose.tools.eq_(
            self.url,
            expected_url,
            "Crowdfund URL <"
            + self.url
            + "> should match expected URL <"
            + expected_url
            + ">",
        )

    def test_crowdfund_view(self):
        """The url should actually resolve to a view."""
        resolver = resolve(self.url)
        nose.tools.eq_(
            resolver.view_name,
            "foia-crowdfund",
            'Crowdfund view name "'
            + resolver.view_name
            + '" should match "foia-crowdfund"',
        )

    def test_crowdfund_view_requires_login(self):
        """Logged out users should be redirected to the login page"""
        response = self.get_res(None)
        nose.tools.ok_(response.status_code, 302)
        nose.tools.eq_(response.url, "/accounts/login/?next=%s" % self.url)

    def test_crowdfund_view_allows_owner(self):
        """Request owners may create a crowdfund on their request."""
        response = self.get_res(self.foia.user)
        nose.tools.eq_(
            response.status_code,
            200,
            (
                "Above all else crowdfund should totally respond with a 200 OK if"
                " logged in user owns the request. (Responds with %d)"
                % response.status_code
            ),
        )

    def test_crowdfund_view_requires_owner(self):
        """Users who are not the owner cannot start a crowdfund on a request."""
        not_owner = UserFactory()
        response = self.get_res(not_owner)
        nose.tools.eq_(
            response.status_code,
            302,
            (
                "Crowdfund should respond with a 302 redirect if logged in"
                " user is not the owner. (Responds with %d)" % response.status_code
            ),
        )

    def test_crowdfund_view_allows_staff(self):
        """Staff members are the exception to the above rule, they can do whatevs."""
        staff_user = UserFactory(is_staff=True)
        response = self.get_res(staff_user)
        nose.tools.eq_(
            response.status_code,
            200,
            (
                "Crowdfund should respond with a 200 OK if logged in user"
                " is a staff member. (Responds with %d)" % response.status_code
            ),
        )

    def test_crowdfund_view_crowdfund_already_exists(self):
        """A crowdfund cannot be created for a request that already has one, even if expired."""
        date_due = timezone.now() + datetime.timedelta(30)
        self.foia.crowdfund = Crowdfund.objects.create(date_due=date_due)
        self.foia.save()
        response = self.get_res(self.foia.user)
        nose.tools.eq_(
            response.status_code,
            302,
            (
                "If a request already has a crowdfund, trying to create a new one "
                "should respond with 302 status code. (Responds with %d)"
                % response.status_code
            ),
        )

    def test_crowdfund_view_payment_not_required(self):
        """A crowdfund can only be created for a request with a status of 'payment'"""
        self.foia.status = "submitted"
        self.foia.save()
        response = self.get_res(self.foia.user)
        nose.tools.eq_(
            response.status_code,
            302,
            (
                'If a request does not have a "Payment Required" status, should '
                "respond with a 302 status code. (Responds with %d)"
                % response.status_code
            ),
        )

    def test_crowdfund_creation(self):
        """Creating a crowdfund should associate it with the request."""
        name = "Request Crowdfund"
        description = "A crowdfund"
        payment_required = 100
        payment_capped = True
        date_due = datetime.date.today() + datetime.timedelta(20)
        data = {
            "name": name,
            "description": description,
            "payment_required": payment_required,
            "payment_capped": payment_capped,
            "date_due": date_due,
        }
        response = self.post_res(self.foia.user, data)
        nose.tools.eq_(
            response.status_code, 302, "The request should redirect to the FOIA."
        )
        self.foia.refresh_from_db()
        nose.tools.ok_(
            self.foia.crowdfund,
            "The crowdfund should be created and associated with the FOIA.",
        )


class TestRequestSharingViews(TestCase):
    """Tests access and implementation of view methods for sharing requests."""

    def setUp(self):
        self.factory = RequestFactory()
        self.foia = FOIARequestFactory()
        self.creator = self.foia.user
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.staff = UserFactory(is_staff=True)
        self.normie = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.foia.save()
        UserFactory(username="MuckrockStaff")

    def reset_access_key(self):
        """Simple helper to reset access key betweeen tests"""
        self.foia.access_key = None
        assert_false(self.foia.access_key)

    def test_access_key_allowed(self):
        """
        A POST request for a private share link should generate and return an access key.
        Editors and staff should be allowed to do this.
        """
        self.reset_access_key()
        data = {"action": "generate_key"}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # editors should be able to generate the key
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(self.foia.access_key)
        # staff should be able to generate the key
        self.reset_access_key()
        request.user = self.staff
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(self.foia.access_key)

    def test_access_key_not_allowed(self):
        """Visitors and normies should not be allowed to generate an access key."""
        self.reset_access_key()
        data = {"action": "generate_key"}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # viewers should not be able to generate the key
        request.user = self.viewer
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_false(self.foia.access_key)
        # normies should not be able to generate the key
        self.reset_access_key()
        request.user = self.normie
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_false(self.foia.access_key)

    def test_grant_edit_access(self):
        """Editors should be able to add editors."""
        user1 = UserFactory()
        user2 = UserFactory()
        edit_data = {
            "action": "grant_access",
            "users": [user1.pk, user2.pk],
            "access": "edit",
        }
        edit_request = self.factory.post(self.foia.get_absolute_url(), edit_data)
        edit_request = mock_middleware(edit_request)
        edit_request.user = self.editor
        edit_response = Detail.as_view()(
            edit_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(edit_response.status_code, 302)
        assert_true(self.foia.has_editor(user1) and self.foia.has_editor(user2))

    def test_grant_view_access(self):
        """Editors should be able to add viewers."""
        user1 = UserFactory()
        user2 = UserFactory()
        view_data = {
            "action": "grant_access",
            "users": [user1.pk, user2.pk],
            "access": "view",
        }
        view_request = self.factory.post(self.foia.get_absolute_url(), view_data)
        view_request = mock_middleware(view_request)
        view_request.user = self.editor
        view_response = Detail.as_view()(
            view_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(view_response.status_code, 302)
        assert_true(self.foia.has_viewer(user1) and self.foia.has_viewer(user2))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        user = UserFactory()
        self.foia.add_editor(user)
        assert_true(self.foia.has_editor(user))
        data = {"action": "demote", "user": user.pk}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_editor(user))
        assert_true(self.foia.has_viewer(user))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        user = UserFactory()
        self.foia.add_viewer(user)
        assert_true(self.foia.has_viewer(user))
        data = {"action": "promote", "user": user.pk}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_viewer(user))
        assert_true(self.foia.has_editor(user))

    def test_revoke_edit_access(self):
        """Editors should be able to revoke access from an editor."""
        an_editor = UserFactory()
        self.foia.add_editor(an_editor)
        data = {"action": "revoke_access", "user": an_editor.pk}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_editor(an_editor))

    def test_revoke_view_access(self):
        """Editors should be able to revoke access from a viewer."""
        a_viewer = UserFactory()
        self.foia.add_viewer(a_viewer)
        data = {"action": "revoke_access", "user": a_viewer.pk}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id,
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_viewer(a_viewer))


class TestFOIAComposerViews(TestCase):
    """Tests for FOIA Composer views"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.mocker = requests_mock.Mocker()
        mock_squarelet(self.mocker)
        self.mocker.start()
        self.addCleanup(self.mocker.stop)
        FOIATemplateFactory.create()

    def test_get_create_composer(self):
        """Get the create composer form"""
        request = self.request_factory.get(reverse("foia-create"))
        request.user = UserFactory()
        request = mock_middleware(request)
        response = CreateComposer.as_view()(request)
        eq_(response.status_code, 200)

    def test_get_create_composer_clone(self):
        """Test cloning a composer"""
        clone = FOIARequestFactory()
        request = self.request_factory.get(
            reverse("foia-create") + "?clone={}".format(clone.composer.pk)
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        response = CreateComposer.as_view()(request)
        eq_(response.status_code, 200)
        eq_(response.context_data["form"].initial["title"], clone.composer.title)

    def test_get_create_composer_anonymous(self):
        """Get the create composer form as an anoynmous user"""
        request = self.request_factory.get(reverse("foia-create"))
        request.user = AnonymousUser()
        request = mock_middleware(request)
        response = CreateComposer.as_view()(request)
        eq_(response.status_code, 200)

    def test_post_create_composer_anonymous(self):
        """Create a new composer as an anonymous user"""
        agency = AgencyFactory()
        data = {
            "title": "Title",
            "requested_docs": "ABC",
            "agencies": agency.pk,
            "action": "save",
            "register_full_name": "John Doe",
            "register_email": "john@example.com",
            "stripe_pk": "STRIPE_PK",
        }
        request = self.request_factory.post(reverse("foia-create"), data)
        request.user = AnonymousUser()
        request = mock_middleware(request)
        response = CreateComposer.as_view()(request)
        eq_(response.status_code, 302)
        user = User.objects.get(email="john@example.com")
        ok_(user.composers.get(title="Title"))

    def test_get_update_composer(self):
        """Get the update composer form"""
        composer = FOIAComposerFactory()
        request = self.request_factory.get(
            reverse("foia-draft", kwargs={"idx": composer.pk})
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = UpdateComposer.as_view()(request, idx=composer.pk)
        eq_(response.status_code, 200)

    def test_get_update_composer_bad(self):
        """Try to update a composer that can no longer be updated"""
        composer = FOIAComposerFactory(status="filed")
        request = self.request_factory.get(
            reverse("foia-draft", kwargs={"idx": composer.pk})
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = UpdateComposer.as_view()(request, idx=composer.pk)
        eq_(response.status_code, 302)

    def test_get_update_composer_revoke(self):
        """Get the update composer form for a recently submitted composer"""
        composer = FOIAComposerFactory(
            status="submitted", delayed_id="123", datetime_submitted=timezone.now()
        )
        request = self.request_factory.get(
            reverse("foia-draft", kwargs={"idx": composer.pk})
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = UpdateComposer.as_view()(request, idx=composer.pk)
        eq_(response.status_code, 200)
        composer.refresh_from_db()
        eq_(composer.status, "started")

    def test_post_update_composer(self):
        """Test submitting a composer"""
        composer = FOIAComposerFactory(status="started")
        agency = AgencyFactory()
        data = {
            "title": "Title",
            "requested_docs": "ABC",
            "agencies": agency.pk,
            "action": "submit",
            "stripe_pk": "STRIPE_PK",
        }
        request = self.request_factory.post(
            reverse("foia-draft", kwargs={"idx": composer.pk}), data
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = UpdateComposer.as_view()(request, idx=composer.pk)
        eq_(response.status_code, 302)
        composer.refresh_from_db()
        ok_(composer.status, "submitted")

    def test_post_delete_update_composer(self):
        """Test deleting a composer"""
        composer = FOIAComposerFactory(status="started")
        data = {"action": "delete"}
        request = self.request_factory.post(
            reverse("foia-draft", kwargs={"idx": composer.pk}), data
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = UpdateComposer.as_view()(request, idx=composer.pk)
        eq_(response.status_code, 302)
        assert_false(FOIAComposer.objects.filter(pk=composer.pk).exists())

    def test_autosave_good(self):
        """Test a succesful autosave"""
        composer = FOIAComposerFactory(status="started")
        request = self.request_factory.post(
            reverse("foia-autosave", kwargs={"idx": composer.pk}),
            {"title": "New Title", "requested_docs": "ABC"},
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = autosave(request, idx=composer.pk)
        eq_(response.status_code, 200)
        composer.refresh_from_db()
        eq_(composer.title, "New Title")
        eq_(composer.requested_docs, "ABC")

    def test_autosave_bad(self):
        """Test a failed autosave"""
        composer = FOIAComposerFactory(status="started")
        request = self.request_factory.post(
            reverse("foia-autosave", kwargs={"idx": composer.pk}),
            {"agencies": "foobar", "requested_docs": "ABC"},
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = autosave(request, idx=composer.pk)
        eq_(response.status_code, 400)

    def test_composer_detail_draft(self):
        """Composer detail view redirects to update page if draft"""
        composer = FOIAComposerFactory(status="started")
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = composer.user
        request = mock_middleware(request)
        response = ComposerDetail.as_view()(
            request, slug=composer.slug, idx=composer.pk
        )
        eq_(response.status_code, 302)
        eq_(response.url, reverse("foia-draft", kwargs={"idx": composer.pk}))

    @raises(Http404)
    def test_composer_detail_draft_bad(self):
        """Composer detail view redirects to update page if draft"""
        composer = FOIAComposerFactory(status="started")
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        ComposerDetail.as_view()(request, slug=composer.slug, idx=composer.pk)

    @raises(Http404)
    def test_composer_detail_private(self):
        """Composer is private if no viewable foias"""
        foia = FOIARequestFactory(
            embargo=True,
            date_embargo=date.today() + timedelta(1),
            composer__status="filed",
        )
        composer = foia.composer
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        ComposerDetail.as_view()(request, slug=composer.slug, idx=composer.pk)

    def test_composer_detail_single(self):
        """Composer redirects to foia page if only a single request"""
        foia = FOIARequestFactory(composer__status="filed")
        composer = foia.composer
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        response = ComposerDetail.as_view()(
            request, slug=composer.slug, idx=composer.pk
        )
        eq_(response.status_code, 302)
        eq_(response.url, foia.get_absolute_url())

    def test_composer_detail_single_submitted(self):
        """Composer redirects to foia page if only a single request even
        if it hasn't been filed yet"""
        foia = FOIARequestFactory(
            composer__status="submitted", composer__datetime_submitted=timezone.now()
        )
        composer = foia.composer
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        response = ComposerDetail.as_view()(
            request, slug=composer.slug, idx=composer.pk
        )
        eq_(response.status_code, 302)
        eq_(response.url, foia.get_absolute_url())

    def test_composer_detail_multi(self):
        """Composer shows its own page if multiple foias"""
        foia = FOIARequestFactory(composer__status="filed")
        FOIARequestFactory(composer=foia.composer)
        composer = foia.composer
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        response = ComposerDetail.as_view()(
            request, slug=composer.slug, idx=composer.pk
        )
        eq_(response.status_code, 200)
        eq_(response.template_name, ["foia/foiacomposer_detail.html"])

    def test_composer_detail_multi_submitted(self):
        """Composer shows its own page if multiple foias"""
        foia = FOIARequestFactory(
            composer__status="submitted", composer__datetime_submitted=timezone.now()
        )
        FOIARequestFactory(composer=foia.composer)
        composer = foia.composer
        request = self.request_factory.get(
            reverse(
                "foia-composer-detail",
                kwargs={"slug": composer.slug, "idx": composer.pk},
            )
        )
        request.user = UserFactory()
        request = mock_middleware(request)
        response = ComposerDetail.as_view()(
            request, slug=composer.slug, idx=composer.pk
        )
        eq_(response.status_code, 200)
        eq_(response.template_name, ["foia/foiacomposer_detail.html"])
