"""
Tests using nose for the FOIA application
"""

# allow methods that could be functions and too many public methods in tests
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines
# pylint: disable=invalid-name

# Django
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# Standard Library
import re
from datetime import date, datetime, timedelta

# Third Party
import nose.tools
import pytz
import requests_mock
from actstream.actions import follow
from freezegun import freeze_time
from nose.tools import eq_, ok_

# MuckRock
from muckrock.core.factories import AgencyFactory, AppealAgencyFactory, UserFactory
from muckrock.core.test_utils import RunCommitHooksMixin, mock_squarelet
from muckrock.core.utils import new_action
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAComposerFactory,
    FOIAFileFactory,
    FOIARequestFactory,
    FOIATemplateFactory,
)
from muckrock.foia.models import FOIACommunication, FOIARequest, RawEmail
from muckrock.task.models import PaymentInfoTask, SnailMailTask


class TestFOIARequestUnit(RunCommitHooksMixin, TestCase):
    """Unit tests for FOIARequests"""

    def setUp(self):
        """Set up tests"""

        mail.outbox = []

        self.foia = FOIARequestFactory(status="submitted", title="Test 1")
        UserFactory(username="MuckrockStaff")

    # models
    def test_foia_model_str(self):
        """Test FOIA Request model's __str__ method"""
        nose.tools.eq_(str(self.foia), "Test 1")

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(
            self.foia.get_absolute_url(),
            reverse(
                "foia-detail",
                kwargs={
                    "idx": self.foia.pk,
                    "slug": "test-1",
                    "jurisdiction": "massachusetts",
                    "jidx": self.foia.jurisdiction.pk,
                },
            ),
        )

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = UserFactory()
        user2 = UserFactory()

        foias = [
            FOIARequestFactory(composer__user=user1, status="done", embargo=False),
            FOIARequestFactory(composer__user=user1, status="done", embargo=True),
            FOIARequestFactory(composer__user=user1, status="done", embargo=True),
        ]
        foias[2].add_viewer(user2)

        # check manager get_viewable against view permission
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(user1, "view"))
            else:
                nose.tools.assert_false(foia.has_perm(user1, "view"))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(user2, "view"))
            else:
                nose.tools.assert_false(foia.has_perm(user2, "view"))

        viewable_foias = FOIARequest.objects.get_public()
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(AnonymousUser(), "view"))
            else:
                nose.tools.assert_false(foia.has_perm(AnonymousUser(), "view"))

        nose.tools.assert_true(foias[0].has_perm(user1, "view"))
        nose.tools.assert_true(foias[1].has_perm(user1, "view"))
        nose.tools.assert_true(foias[2].has_perm(user1, "view"))

        nose.tools.assert_true(foias[0].has_perm(user2, "view"))
        nose.tools.assert_false(foias[1].has_perm(user2, "view"))
        nose.tools.assert_true(foias[2].has_perm(user2, "view"))

        nose.tools.assert_true(foias[0].has_perm(AnonymousUser(), "view"))
        nose.tools.assert_false(foias[1].has_perm(AnonymousUser(), "view"))
        nose.tools.assert_false(foias[2].has_perm(AnonymousUser(), "view"))

    def test_foia_viewable_org_share(self):
        """Test all the viewable and embargo functions"""
        user = UserFactory()
        foia = FOIARequestFactory(
            embargo=True, composer__organization=user.profile.organization
        )
        foias = FOIARequest.objects.get_viewable(user)
        nose.tools.assert_not_in(foia, foias)

        foia.user.profile.org_share = True
        foia.user.profile.save()
        foias = FOIARequest.objects.get_viewable(user)
        nose.tools.assert_in(foia, foias)

    def test_foia_set_mail_id(self):
        """Test the set_mail_id function"""
        foia = FOIARequestFactory()
        foia.set_mail_id()
        mail_id = foia.mail_id
        nose.tools.ok_(re.match(r"\d{1,4}-\d{8}", mail_id))

        foia.set_mail_id()
        nose.tools.eq_(mail_id, foia.mail_id)

    def test_foia_followup(self):
        """Make sure the follow up date is set correctly"""
        # pylint: disable=protected-access
        foia = FOIARequestFactory(
            composer__datetime_submitted=timezone.now(),
            status="processed",
            agency__jurisdiction__level="s",
            agency__jurisdiction__law__days=10,
        )
        FOIACommunicationFactory(foia=foia, response=True)
        foia.followup()
        self.run_commit_hooks()
        nose.tools.assert_in("I can expect", mail.outbox[-1].body)
        nose.tools.eq_(
            foia.date_followup,
            foia.communications.last().datetime.date()
            + timedelta(foia._followup_days()),
        )

        nose.tools.eq_(foia._followup_days(), 15)

        num_days = 365
        foia.date_estimate = date.today() + timedelta(num_days)
        foia.followup()
        self.run_commit_hooks()
        nose.tools.assert_in("I am still", mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), num_days)

        foia.date_estimate = date.today()
        foia.followup()
        self.run_commit_hooks()
        nose.tools.assert_in("check on the status", mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), 15)

    def test_foia_followup_estimated(self):
        """If request has an estimated date, returns number of days until the estimated date"""
        # pylint: disable=protected-access
        num_days = 365
        foia = FOIARequestFactory(date_estimate=date.today() + timedelta(num_days))
        nose.tools.eq_(foia._followup_days(), num_days)

    def test_manager_get_done(self):
        """Test the FOIA Manager's get_done method"""

        done_foias = FOIARequest.objects.get_done()
        for foia in FOIARequest.objects.all():
            if foia in done_foias:
                nose.tools.eq_(foia.status, "done")
            else:
                nose.tools.assert_in(
                    foia.status,
                    ["submitted", "processed", "fix", "rejected", "payment"],
                )

    def test_soft_delete(self):
        """Test the soft delete method"""
        foia = FOIARequestFactory(status="processed")
        FOIAFileFactory.create_batch(size=3, comm__foia=foia)
        user = UserFactory(is_superuser=True)

        nose.tools.eq_(foia.get_files().count(), 3)
        nose.tools.eq_(
            RawEmail.objects.filter(email__communication__foia=foia).count(), 3
        )

        foia.soft_delete(user, "final message", "note")
        foia.refresh_from_db()
        self.run_commit_hooks()

        # final communication we send out is not cleared
        for comm in list(foia.communications.all())[:-1]:
            nose.tools.eq_(comm.communication, "")
        nose.tools.eq_(foia.get_files().count(), 0)
        # one raw email left on the final outgoing message
        nose.tools.eq_(
            RawEmail.objects.filter(email__communication__foia=foia).count(), 1
        )
        nose.tools.eq_(foia.last_request().communication, "final message")
        nose.tools.eq_(foia.notes.first().note, "note")

        nose.tools.ok_(foia.deleted)
        nose.tools.ok_(foia.embargo)
        nose.tools.ok_(foia.permanent_embargo)
        nose.tools.eq_(foia.status, "abandoned")


class TestFOIAIntegration(RunCommitHooksMixin, TestCase):
    """Integration tests for FOIA"""

    @requests_mock.Mocker()
    def test_request_lifecycle_no_email(self, mock_request):
        """Test a request going through the full cycle as if we had to
        physically mail it
        """
        # pylint: disable=too-many-statements
        # pylint: disable=protected-access

        FOIATemplateFactory.create()

        mock_squarelet(mock_request)
        mail.outbox = []
        user = UserFactory(membership__organization__number_requests=1)
        agency = AgencyFactory(email=None, fax=None)
        cal = agency.jurisdiction.get_calendar()

        with freeze_time("2010-02-01"):
            nose.tools.eq_(len(mail.outbox), 0)

            ## create and submit request
            composer = FOIAComposerFactory(
                user=user,
                organization=user.profile.organization,
                title="Test with no email",
                agencies=[agency],
            )
            composer.submit()
            foia = FOIARequest.objects.get(composer=composer)
            comm = foia.communications.last()
            self.run_commit_hooks()

            # check that a snail mail task was created
            nose.tools.ok_(
                SnailMailTask.objects.filter(communication=comm, category="n").exists()
            )

        ## two days pass, then the admin mails in the request
        with freeze_time("2010-02-03"):
            foia.status = "processed"
            foia.update_dates()
            foia.save()

            # make sure dates were set correctly
            nose.tools.eq_(
                foia.composer.datetime_submitted, datetime(2010, 2, 1, tzinfo=pytz.utc)
            )
            nose.tools.eq_(
                foia.date_due,
                cal.business_days_from(date(2010, 2, 1), agency.jurisdiction.days),
            )
            nose.tools.eq_(
                foia.date_followup,
                max(
                    foia.date_due,
                    foia.communications.last().datetime.date()
                    + timedelta(foia._followup_days()),
                ),
            )
            nose.tools.ok_(foia.days_until_due is None)
            # no more mail should have been sent
            nose.tools.eq_(len(mail.outbox), 0)

            old_date_due = foia.date_due

        ## after 5 days agency replies with a fix needed
        with freeze_time("2010-02-08"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=agency.get_user(),
                to_user=user,
                datetime=timezone.now(),
                response=True,
                communication="Test communication",
            )
            foia.status = "fix"
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(
                foia.composer.datetime_submitted, datetime(2010, 2, 1, tzinfo=pytz.utc)
            )
            nose.tools.ok_(foia.date_due is None)
            nose.tools.ok_(foia.date_followup is None)
            nose.tools.eq_(
                foia.days_until_due,
                cal.business_days_between(date(2010, 2, 8), old_date_due),
            )

            old_days_until_due = foia.days_until_due

        ## after 10 days the user submits the fix and the admin submits it right away
        with freeze_time("2010-02-18"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=user,
                to_user=agency.get_user(),
                datetime=timezone.now(),
                response=False,
                communication="Test communication",
            )
            foia.status = "submitted"
            foia.save()
            foia.submit()
            self.run_commit_hooks()

            # check that another snail mail task is created
            nose.tools.ok_(
                SnailMailTask.objects.filter(communication=comm, category="u").exists()
            )

            foia.status = "processed"

            foia.update_dates()
            foia.save()

            # make sure dates were set correctly
            nose.tools.eq_(
                foia.composer.datetime_submitted, datetime(2010, 2, 1, tzinfo=pytz.utc)
            )
            nose.tools.eq_(
                foia.date_due, cal.business_days_from(date.today(), old_days_until_due)
            )
            nose.tools.eq_(
                foia.date_followup,
                max(
                    foia.date_due,
                    foia.communications.last().datetime.date()
                    + timedelta(foia._followup_days()),
                ),
            )
            nose.tools.ok_(foia.days_until_due is None)

            old_date_due = foia.date_due

        ## after 4 days agency replies with the documents
        with freeze_time("2010-02-22"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=agency.get_user(),
                to_user=user,
                datetime=timezone.now(),
                response=True,
                communication="Test communication",
            )
            foia.status = "done"
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(
                foia.composer.datetime_submitted, datetime(2010, 2, 1, tzinfo=pytz.utc)
            )
            nose.tools.eq_(foia.date_due, old_date_due)
            nose.tools.ok_(foia.date_followup is None)
            nose.tools.ok_(foia.days_until_due is None)


class TestFOIARequestAppeal(RunCommitHooksMixin, TestCase):
    """A request should be able to send an appeal to the agency that receives them."""

    def setUp(self):
        self.appeal_agency = AppealAgencyFactory()
        self.agency = AgencyFactory(status="approved", appeal_agency=self.appeal_agency)
        self.foia = FOIARequestFactory(agency=self.agency, status="rejected")

    def test_appeal(self):
        """Sending an appeal to the agency should require the message for the appeal,
        which is then turned into a communication to the correct agency. In this case,
        the correct agency is the same one that received the message."""
        ok_(
            self.foia.has_perm(self.foia.user, "appeal"),
            "The request should be appealable.",
        )
        ok_(
            self.agency and self.agency.status == "approved",
            "The agency should be approved.",
        )
        ok_(
            self.appeal_agency.get_emails("appeal"),
            "The appeal agency should accept email.",
        )
        # Create the appeal message and submit it
        appeal_message = "Lorem ipsum"
        appeal_comm = self.foia.appeal(appeal_message, self.foia.user)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        self.run_commit_hooks()
        eq_(self.foia.email, self.appeal_agency.get_emails("appeal").first())
        eq_(self.foia.status, "appealing")
        eq_(appeal_comm.communication, appeal_message)
        eq_(appeal_comm.from_user, self.foia.user)
        eq_(appeal_comm.to_user, self.agency.get_user())
        ok_(appeal_comm.emails.exists())

    def test_mailed_appeal(self):
        """Sending an appeal to an agency via mail should set the request to 'submitted',
        create a snail mail task with the 'a' category, and set the appeal communication
        delivery method to 'mail'."""
        # Make the appeal agency unreceptive to emails
        self.appeal_agency.emails.clear()
        # Create the appeal message and submit it
        appeal_message = "Lorem ipsum"
        appeal_comm = self.foia.appeal(appeal_message, self.foia.user)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        self.run_commit_hooks()
        eq_(
            self.foia.status,
            "submitted",
            "The status of the request should be updated. Actually: %s"
            % self.foia.status,
        )
        eq_(
            appeal_comm.communication,
            appeal_message,
            "The appeal message parameter should be used as the body of the communication.",
        )
        eq_(
            appeal_comm.from_user,
            self.foia.user,
            "The appeal should be addressed from the request owner.",
        )
        eq_(
            appeal_comm.to_user,
            self.agency.get_user(),
            "The appeal should be addressed to the agency.",
        )
        task = SnailMailTask.objects.get(communication=appeal_comm)
        ok_(task, "A snail mail task should be created.")
        eq_(task.category, "a")


class TestRequestPayment(RunCommitHooksMixin, TestCase):
    """Allow users to pay fees on a request"""

    def setUp(self):
        self.foia = FOIARequestFactory()
        UserFactory(username="MuckrockStaff")

    def test_make_payment(self):
        """The request should accept payments for request fees."""
        user = self.foia.user
        amount = 100.0
        comm = self.foia.pay(user, amount)
        self.run_commit_hooks()
        self.foia.refresh_from_db()
        eq_(self.foia.status, "submitted")
        eq_(self.foia.date_processing, date.today())
        ok_(comm, "The function should return a communication.")
        task = PaymentInfoTask.objects.filter(communication=comm).first()
        ok_(task, "A payment info task should be created.")
        eq_(task.amount, amount)


class TestRequestSharing(TestCase):
    """Allow people to edit and view another user's request."""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.editor = UserFactory()
        self.creator = self.foia.user

    def test_add_editor(self):
        """Editors should be able to add editors to the request."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        nose.tools.assert_true(self.foia.has_editor(new_editor))

    def test_remove_editor(self):
        """Editors should be able to remove editors from the request."""
        editor_to_remove = self.editor
        # first we add the editor, otherwise we would have nothing to remove!
        self.foia.add_editor(editor_to_remove)
        nose.tools.assert_true(self.foia.has_editor(editor_to_remove))
        # now we remove the editor we just added
        self.foia.remove_editor(editor_to_remove)
        nose.tools.assert_false(self.foia.has_editor(editor_to_remove))

    def test_editor_permission(self):
        """Editors should have the same abilities and permissions as creators."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        nose.tools.ok_(self.foia.has_perm(new_editor, "change"))

    def test_add_viewer(self):
        """Editors should be able to add viewers to the request."""
        new_viewer = UserFactory()
        self.foia.add_viewer(new_viewer)
        nose.tools.ok_(self.foia.has_viewer(new_viewer))

    def test_remove_viewer(self):
        """Editors should be able to remove viewers from the request."""
        viewer_to_remove = UserFactory()
        # first we add the viewer, otherwise we would have nothing to remove!
        self.foia.add_viewer(viewer_to_remove)
        nose.tools.ok_(self.foia.has_viewer(viewer_to_remove))
        # now we remove the viewer we just added
        self.foia.remove_viewer(viewer_to_remove)
        nose.tools.assert_false(self.foia.has_viewer(viewer_to_remove))

    def test_viewer_permission(self):
        """Viewers should be able to see the request if it is embargoed."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        normie = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, "view"))
        nose.tools.assert_false(embargoed_foia.has_perm(normie, "view"))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, "view"))
        nose.tools.assert_false(embargoed_foia.has_perm(viewer, "change"))
        embargoed_foia.promote_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, "change"))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        nose.tools.assert_true(embargoed_foia.has_perm(editor, "view"))
        nose.tools.assert_true(embargoed_foia.has_perm(editor, "change"))
        embargoed_foia.demote_editor(editor)
        nose.tools.assert_false(embargoed_foia.has_perm(editor, "change"))

    def test_access_key(self):
        """Editors should be able to generate a secure access key to view an embargoed request."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        access_key = embargoed_foia.generate_access_key()
        nose.tools.assert_true(
            access_key == embargoed_foia.access_key,
            "The key in the URL should match the key saved to the request.",
        )
        embargoed_foia.generate_access_key()
        nose.tools.assert_false(
            access_key == embargoed_foia.access_key,
            "After regenerating the link, the key should no longer match.",
        )

    def test_do_not_grant_creator_access(self):
        """Creators should not be granted access as editors or viewers"""
        self.foia.add_editor(self.creator)
        nose.tools.assert_false(self.foia.has_editor(self.creator))
        self.foia.add_viewer(self.creator)
        nose.tools.assert_false(self.foia.has_viewer(self.creator))
        # but the creator should still be able to both view and edit!
        nose.tools.assert_true(self.foia.has_perm(self.creator, "change"))
        nose.tools.assert_true(self.foia.has_perm(self.creator, "view"))


class TestFOIANotification(TestCase):
    """The request should always notify its owner,
    but only notify followers if its not embargoed."""

    def setUp(self):
        agency = AgencyFactory()
        self.owner = UserFactory()
        self.follower = UserFactory()
        self.request = FOIARequestFactory(composer__user=self.owner, agency=agency)
        follow(self.follower, self.request)
        self.action = new_action(agency, "completed", target=self.request)

    def test_owner_notified(self):
        """The owner should always be notified."""
        # unembargoed
        notification_count = self.owner.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.count(),
            notification_count + 1,
            "The owner should get a new notification.",
        )
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.owner.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.count(),
            notification_count + 1,
            "The owner should get a new notification.",
        )

    def test_follower_notified(self):
        """The owner should always be notified."""
        # unembargoed
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.follower.notifications.count(),
            notification_count + 1,
            "A follower should get a new notification when unembargoed.",
        )
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.follower.notifications.count(),
            notification_count,
            "A follower should not get a new notification when embargoed.",
        )

    def test_identical_notification(self):
        """A new notification should mark any with identical language as read."""
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 1)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count,
            "Any similar notifications should be marked as read.",
        )

    def test_unidentical_notification(self):
        """A new notification shoudl not mark any with unidentical language as read."""
        first_action = new_action(self.request.agency, "completed", target=self.request)
        second_action = new_action(self.request.agency, "rejected", target=self.request)
        third_action = new_action(self.owner, "completed", target=self.request)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(first_action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count + 1,
            "The user should have one unread notification.",
        )
        self.request.notify(second_action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count + 2,
            "The user should have two unread notifications.",
        )
        self.request.notify(third_action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count + 3,
            "The user should have three unread notifications.",
        )

    def test_idential_different_requests(self):
        """An identical action on a different request should not mark anything as read."""
        other_request = FOIARequestFactory(
            composer__user=self.owner, agency=self.request.agency
        )
        other_action = new_action(
            self.request.agency, "completed", target=other_request
        )
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count + 1,
            "The user should have one unread notification.",
        )
        other_request.notify(other_action)
        eq_(
            self.owner.notifications.get_unread().count(),
            unread_count + 2,
            "The user should have two unread notifications.",
        )
