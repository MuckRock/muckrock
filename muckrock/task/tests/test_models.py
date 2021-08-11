"""
Tests for Tasks models
"""

# Django
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

# Standard Library
import logging

# Third Party
import mock
import requests_mock
from nose.tools import assert_false, eq_, ok_, raises

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.core.test_utils import mock_squarelet
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAComposerFactory,
    FOIARequestFactory,
)
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.factories import StateJurisdictionFactory
from muckrock.task.factories import FlaggedTaskFactory, ProjectReviewTaskFactory
from muckrock.task.forms import ResponseTaskForm
from muckrock.task.models import (
    BlacklistDomain,
    FlaggedTask,
    MultiRequestTask,
    NewAgencyTask,
    OrphanTask,
    ResponseTask,
    SnailMailTask,
    StatusChangeTask,
    Task,
)
from muckrock.task.pdf import SnailMailPDF
from muckrock.task.signals import domain_blacklist

mock_send = mock.Mock()

# pylint: disable=missing-docstring
# pylint: disable=protected-access


class TaskTests(TestCase):
    """Test the Task base class"""

    def setUp(self):
        self.task = Task.objects.create()

    def test_task_creates_successfully(self):
        ok_(self.task, "Tasks given no arguments should create successfully")

    def test_unicode(self):
        eq_(
            str(self.task),
            "Task",
            "Unicode string should return the classname of the task",
        )

    def test_resolve(self):
        """Tasks should be resolvable, updating their state when that happens."""
        self.task.resolve()
        ok_(
            self.task.resolved is True,
            "Resolving task should set resolved field to True",
        )
        ok_(self.task.date_done is not None, "Resolving task should set date_done")
        ok_(
            self.task.resolved_by is None,
            "Resolving without providing a user should leave the field blank.",
        )

    def test_resolve_with_user(self):
        """Tasks should record the user responsible for the resolution."""
        user = UserFactory()
        self.task.resolve(user)
        eq_(
            self.task.resolved_by,
            user,
            "The resolving user should be recorded by the task.",
        )


class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    def setUp(self):
        self.comm = FOIACommunicationFactory(
            email__from_email__email="test@example.com"
        )
        self.task = OrphanTask.objects.create(
            reason="ib", communication=self.comm, address="Whatever Who Cares"
        )
        self.user = UserFactory()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse("orphan-task", kwargs={"pk": self.task.pk}),
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            "Orphan tasks given reason and communication arguments should create successfully",
        )

    def test_move(self):
        """Should move the communication to the listed requests and create a
        ResponseTask for each new communication.
        """
        foia1 = FOIARequestFactory()
        foia2 = FOIARequestFactory()
        foia3 = FOIARequestFactory()
        count_response_tasks = ResponseTask.objects.count()
        self.task.move([foia1.pk, foia2.pk, foia3.pk], self.user)
        eq_(
            ResponseTask.objects.count(),
            count_response_tasks + 3,
            "Reponse tasks should be created for each communication moved.",
        )

    def test_get_sender_domain(self):
        """Should return the domain of the orphan's sender."""
        eq_(self.task.get_sender_domain(), "example.com")

    def test_reject(self):
        """Shouldn't do anything, ATM. Revisit later."""
        self.task.reject()

    def test_blacklist(self):
        """A blacklisted orphan should add its sender's domain to the blacklist"""
        self.task.blacklist()
        ok_(BlacklistDomain.objects.filter(domain="example.com"))

    def test_blacklist_duplicate(self):
        """The blacklist method should not crash when a domain is dupliacted."""
        BlacklistDomain.objects.create(domain="muckrock.com")
        BlacklistDomain.objects.create(domain="muckrock.com")
        self.task.blacklist()
        ok_(BlacklistDomain.objects.filter(domain="muckrock.com"))

    def test_resolve_after_blacklisting(self):
        """After blacklisting, other orphan tasks from the sender should be resolved."""
        other_task = OrphanTask.objects.create(
            reason="ib", communication=self.comm, address="Whatever Who Cares"
        )
        self.task.blacklist()
        self.task.refresh_from_db()
        other_task.refresh_from_db()
        ok_(self.task.resolved and other_task.resolved)

    def test_create_blacklist_sender(self):
        """An orphan created from a blacklisted sender should be automatically resolved."""
        self.task.blacklist()
        self.task.refresh_from_db()
        ok_(self.task.resolved)
        new_orphan = OrphanTask.objects.create(
            reason="ib", communication=self.comm, address="orphan-address"
        )
        # manually call the method since the signal isn't triggering during testing
        domain_blacklist(OrphanTask, new_orphan, True)
        new_orphan.refresh_from_db()
        logging.debug(new_orphan.resolved)
        ok_(new_orphan.resolved)


@mock.patch("muckrock.message.notifications.SlackNotification.send", mock_send)
class FlaggedTaskTests(TestCase):
    """Test the FlaggedTask class"""

    def setUp(self):
        self.task = FlaggedTask

    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def test_get_absolute_url(self):
        text = "Lorem ipsum"
        user = UserFactory()
        foia = FOIARequestFactory()
        flagged_task = self.task.objects.create(user=user, foia=foia, text=text)
        _url = reverse("flagged-task", kwargs={"pk": flagged_task.pk})
        eq_(flagged_task.get_absolute_url(), _url)

    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def test_flagged_object(self):
        """A flagged task should be able to return its object."""
        text = "Lorem ipsum"
        user = UserFactory()
        foia = FOIARequestFactory()
        agency = AgencyFactory()
        jurisdiction = StateJurisdictionFactory()
        flagged_foia_task = self.task.objects.create(user=user, foia=foia, text=text)
        flagged_agency_task = self.task.objects.create(
            user=user, agency=agency, text=text
        )
        flagged_jurisdiction_task = self.task.objects.create(
            user=user, jurisdiction=jurisdiction, text=text
        )
        eq_(flagged_foia_task.flagged_object(), foia)
        eq_(flagged_agency_task.flagged_object(), agency)
        eq_(flagged_jurisdiction_task.flagged_object(), jurisdiction)

    @raises(AttributeError)
    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def test_no_flagged_object(self):
        """Should raise an error if no flagged object"""
        text = "Lorem ipsum"
        user = UserFactory()
        flagged_task = self.task.objects.create(user=user, text=text)
        flagged_task.flagged_object()

    @mock.patch("muckrock.message.tasks.support.delay")
    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def test_reply(self, mock_support):
        """Given a message, a support notification should be sent to the task's user."""
        flagged_task = FlaggedTaskFactory()
        reply = "Lorem ipsum"
        flagged_task.reply(reply)
        mock_support.assert_called_with(flagged_task.user.pk, reply, flagged_task.pk)

    @requests_mock.Mocker()
    def test_create_zoho_ticket(self, mock_requests):
        """Test the creation of a zoho help ticket when a flag is created"""
        mock_requests.get(
            settings.ZOHO_URL + "contacts/search",
            json={"count": 1, "data": [{"id": "contact_id"}]},
        )
        mock_requests.post(settings.ZOHO_URL + "tickets", json={"id": "ticket_id"})
        flagged_task = FlaggedTaskFactory(
            user__email="flag@example.com", text="Example flag text"
        )
        flagged_task.refresh_from_db()
        ok_(flagged_task.resolved)
        eq_(flagged_task.form_data, {"zoho_id": "ticket_id"})

    @override_settings(USE_ZENDESK=True)
    @requests_mock.Mocker()
    def test_create_zend_ticket(self, mock_requests):
        """Test the creation of a zendesk help ticket when a flag is created"""
        mock_requests.post(
            "https://muckrock.zendesk.com/api/v2/organizations/create_or_update.json",
            json={"organization": {"id": "org_id"}},
        )
        mock_requests.post(
            "https://muckrock.zendesk.com/api/v2/users/create_or_update.json",
            json={"user": {"id": "user_id"}},
        )
        mock_requests.post(
            "https://muckrock.zendesk.com/api/v2/tickets.json",
            json={"ticket": {"id": "ticket_id"}, "audit": {}},
        )
        flagged_task = FlaggedTaskFactory(
            user__email="flag@example.com", text="Example flag text"
        )
        flagged_task.refresh_from_db()
        ok_(flagged_task.resolved)
        eq_(flagged_task.form_data, {"zen_id": "ticket_id"})


@mock.patch("muckrock.message.notifications.SlackNotification.send", mock_send)
class ProjectReviewTaskTests(TestCase):
    """
    The ProjectReviewTask provides us a way to moderate community projects.
    When it is created, it should notify Slack.
    When it is approved, it should mark its project approved.
    When it is rejected, it should mark its project private.
    It should allow us a way to communicate with the users of this project.
    """

    def setUp(self):
        self.task = ProjectReviewTaskFactory()
        contributor = UserFactory()
        self.task.project.contributors.add(contributor)

    def test_get_aboslute_url(self):
        _url = reverse("projectreview-task", kwargs={"pk": self.task.pk})
        eq_(self.task.get_absolute_url(), _url)

    @mock.patch("muckrock.message.email.TemplateEmail.send")
    def test_reply(self, mock_feedback_send):
        self.task.reply("Lorem ipsum")
        mock_feedback_send.assert_called_with(fail_silently=False)

    @mock.patch("muckrock.message.email.TemplateEmail.send")
    def test_approve(self, mock_notification_send):
        """Approving the task should mark it approved and notify the contributors."""
        self.task.approve("Lorem ipsum")
        ok_(self.task.project.approved, "The project should be approved")
        mock_notification_send.assert_called_with(fail_silently=False)

    @mock.patch("muckrock.message.email.TemplateEmail.send")
    def test_reject(self, mock_notification_send):
        """Rejecting the task should mark it private and notify the contributors."""
        self.task.reject("Lorem ipsum")
        ok_(self.task.project.private, "The project should be made private.")
        mock_notification_send.assert_called_with(fail_silently=False)


class SnailMailTaskTests(TestCase):
    """Test the SnailMailTask class"""

    def setUp(self):
        self.comm = FOIACommunicationFactory()
        self.task = SnailMailTask.objects.create(category="a", communication=self.comm)

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse("snail-mail-task", kwargs={"pk": self.task.pk}),
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            "Snail mail tasks should create successfully given a category and a communication",
        )

    def test_set_status(self):
        new_status = "ack"
        self.task.set_status(new_status)
        eq_(
            self.task.communication.status,
            new_status,
            "Setting status should update status of associated communication",
        )
        eq_(
            self.task.communication.foia.status,
            new_status,
            "Setting status should update status of associated communication's foia request",
        )

    def test_update_text(self):
        """Snail mail tasks should be able to update the text of their communication."""
        comm = self.task.communication
        new_text = "test"
        self.task.update_text(new_text)
        self.task.refresh_from_db()
        comm.refresh_from_db()
        eq_(
            comm.communication,
            new_text,
            "The text of the communication should be updated.",
        )

    def test_record_check(self):
        """Given a check number, a check should be attached to the communication."""
        user = UserFactory(is_staff=True)
        check_number = 1
        self.task.amount = 100.00
        self.task.save()
        self.task.record_check(check_number, user)
        ok_(self.task.communication.checks.exists())

    def test_pdf_emoji(self):
        """Strip emojis to prevent PDF generation from crashing"""
        comm = FOIACommunicationFactory(communication="Thank you\U0001f60a\n\n")
        pdf = SnailMailPDF(comm, "n", switch=False)
        pdf.generate()
        pdf.output(dest="S").encode("latin-1")


class NewAgencyTaskTests(TestCase):
    """Test the NewAgencyTask class"""

    def setUp(self):
        self.user = UserFactory()
        self.agency = AgencyFactory(status="pending")
        self.task = NewAgencyTask.objects.create(user=self.user, agency=self.agency)

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse("new-agency-task", kwargs={"pk": self.task.pk}),
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            "New agency tasks should create successfully given a user and an agency",
        )

    @mock.patch("muckrock.foia.models.FOIARequest.submit")
    def _test_approve(self, mock_submit):
        submitted_foia = FOIARequestFactory(agency=self.agency, status="submitted")
        FOIACommunicationFactory(foia=submitted_foia)
        self.task.approve()
        eq_(self.task.agency.status, "approved")
        eq_(mock_submit.call_count, 1)

    def test_reject(self):
        replacement = AgencyFactory()
        existing_foia = FOIARequestFactory(agency=self.agency)
        self.task.reject(replacement)
        existing_foia.refresh_from_db()
        eq_(
            self.task.agency.status,
            "rejected",
            "Rejecting a new agency should leave it unapproved.",
        )
        eq_(
            existing_foia.agency,
            replacement,
            "The replacement agency should receive the rejected agency's requests.",
        )

    def test_spam(self):
        moderator = UserFactory()
        existing_foia = FOIARequestFactory(agency=self.agency, status="submitted")
        self.task.spam(moderator)
        eq_(self.agency.status, "rejected")
        assert_false(self.user.is_active)
        assert_false(FOIARequest.objects.filter(pk=existing_foia.pk).exists())


class ResponseTaskTests(TestCase):
    """Test the ResponseTask class"""

    def setUp(self):
        agency = AgencyFactory()
        comm = FOIACommunicationFactory(response=True, foia__agency=agency)
        self.task = ResponseTask.objects.create(communication=comm)
        self.form = ResponseTaskForm(task=self.task)
        self.user = UserFactory()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse("response-task", kwargs={"pk": self.task.pk}),
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            "Response tasks should creates successfully given a communication",
        )

    def test_set_status_to_ack(self):
        self.form.set_status("ack", True, [self.task.communication])
        eq_(
            self.task.communication.foia.datetime_done,
            None,
            "The FOIA should not be set to done if the status does not indicate it is done.",
        )
        eq_(
            self.task.communication.status,
            "ack",
            "The communication should be set to the proper status.",
        )
        eq_(
            self.task.communication.foia.status,
            "ack",
            "The FOIA should be set to the proper status.",
        )

    def test_set_status_to_done(self):
        self.form.set_status("done", True, [self.task.communication])
        eq_(
            self.task.communication.foia.datetime_done is None,
            False,
            "The FOIA should be set to done if the status indicates it is done.",
        )
        eq_(
            self.task.communication.status,
            "done",
            "The communication should be set to the proper status.",
        )
        eq_(
            self.task.communication.foia.status,
            "done",
            "The FOIA should be set to the proper status.",
        )

    def test_set_comm_status_only(self):
        foia = self.task.communication.foia
        existing_status = foia.status
        self.form.set_status("done", False, [self.task.communication])
        foia.refresh_from_db()
        eq_(
            foia.datetime_done is None,
            True,
            "The FOIA should not be set to done because we are not settings its status.",
        )
        eq_(foia.status, existing_status, "The FOIA status should not be changed.")
        eq_(
            self.task.communication.status,
            "done",
            "The Communication status should be changed, however.",
        )

    def test_set_tracking_id(self):
        new_tracking = "dogs-r-cool"
        self.form.set_tracking_id(new_tracking, [self.task.communication])
        self.task.refresh_from_db()
        eq_(
            self.task.communication.foia.current_tracking_id(),
            new_tracking,
            "Should update the tracking number on the request.",
        )

    def test_set_date_estimate(self):
        new_date = timezone.now()
        self.form.set_date_estimate(new_date, [self.task.communication])
        eq_(
            self.task.communication.foia.date_estimate,
            new_date,
            "Should update the estimated completion date on the request.",
        )

    def test_set_price(self):
        price = 1.23
        self.form.set_price(price, [self.task.communication])
        eq_(
            self.task.communication.foia.price,
            price,
            "Should update the price on the request.",
        )

    def test_move(self):
        move_to_foia = FOIARequestFactory()
        self.form.move_communication(
            self.task.communication, [move_to_foia.pk], self.user
        )
        eq_(
            self.task.communication.foia,
            move_to_foia,
            "Should move the communication to a different request.",
        )

    @raises(ValueError)
    def test_bad_status(self):
        """Should raise an error if given a nonexistant status."""
        self.form.set_status("foo", True, [self.task.communication])

    @raises(ValueError)
    def test_bad_tracking_number(self):
        """Should raise an error if not given a string."""
        self.form.set_tracking_id(["foo"], [self.task.communication])

    @raises(ValueError)
    def test_bad_move(self):
        """Should raise a value error if non-existant move destination."""
        self.form.move_communication(self.task.communication, [111111], self.user)

    @raises(ValueError)
    def test_bad_price(self):
        """Should raise an error if not given a value convertable to a float"""
        self.form.set_price("foo", [self.task.communication])


class MultiRequestTaskTests(TestCase):
    """Test the MultiRequestTask class"""

    def setUp(self):
        self.agencies = AgencyFactory.create_batch(6)
        self.composer = FOIAComposerFactory(
            status="submitted",
            agencies=self.agencies,
            num_monthly_requests=2,
            num_reg_requests=3,
        )
        self.task = MultiRequestTask.objects.create(composer=self.composer)

        self.mocker = requests_mock.Mocker()
        mock_squarelet(self.mocker)
        self.mocker.start()
        self.addCleanup(self.mocker.stop)

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse("multirequest-task", kwargs={"pk": self.task.pk}),
        )

    def test_submit(self):
        """Test submitting the task"""
        agency_list = [str(a.pk) for a in self.agencies[:4]]
        self.task.submit(agency_list)
        eq_(set(self.composer.agencies.all()), set(self.agencies[:4]))

    def test_reject(self):
        """Test rejecting the request"""
        self.task.reject()
        eq_(set(self.composer.agencies.all()), set(self.agencies))
        eq_(self.composer.status, "started")
        eq_(FOIARequest.objects.filter(composer=self.composer).count(), 0)


class TestTaskManager(TestCase):
    """Tests for a helpful and handy task object manager."""

    @mock.patch("muckrock.message.notifications.SlackNotification.send", mock_send)
    @mock.patch("muckrock.task.tasks.create_ticket.delay", mock.Mock())
    def setUp(self):
        user = UserFactory()
        agency = AgencyFactory(status="pending")
        self.foia = FOIARequestFactory(composer__user=user, agency=agency)
        self.comm = FOIACommunicationFactory(foia=self.foia, response=True)
        # tasks that incorporate FOIAs are:
        # ResponseTask, SnailMailTask, FlaggedTask,
        # StatusChangeTask, NewAgencyTask
        response_task = ResponseTask.objects.create(communication=self.comm)
        snail_mail_task = SnailMailTask.objects.create(
            category="a", communication=self.comm
        )
        flagged_task = FlaggedTask.objects.create(
            user=user, text="Halp", foia=self.foia
        )
        status_change_task = StatusChangeTask.objects.create(
            user=user, old_status="ack", foia=self.foia
        )
        new_agency_task = NewAgencyTask.objects.create(user=user, agency=agency)
        self.tasks = [
            response_task,
            snail_mail_task,
            flagged_task,
            status_change_task,
            new_agency_task,
        ]

    def test_tasks_for_foia(self):
        """
        The task manager should return all tasks that explictly
        or implicitly reference the provided FOIA.
        """
        staff_user = UserFactory(is_staff=True)
        returned_tasks = Task.objects.filter_by_foia(self.foia, staff_user)
        eq_(
            returned_tasks,
            self.tasks,
            "The manager should return all the tasks that incorporate this FOIA.",
        )
