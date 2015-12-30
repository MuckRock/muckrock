"""
Tests for Tasks models
"""

from django.http import Http404
from django.test import TestCase

from datetime import datetime
import logging
import nose

from muckrock import factories
from muckrock import task
from muckrock.task.signals import domain_blacklist

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

# pylint: disable=missing-docstring
# pylint: disable=line-too-long
# pylint: disable=no-member

class TaskTests(TestCase):
    """Test the Task base class"""

    def setUp(self):
        self.task = task.models.Task.objects.create()

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Tasks given no arguments should create successfully')

    def test_unicode(self):
        eq_(unicode(self.task), u'Task', 'Unicode string should return the classname of the task')

    def test_resolve(self):
        """Tasks should be resolvable, updating their state when that happens."""
        self.task.resolve()
        ok_(self.task.resolved is True,
            'Resolving task should set resolved field to True')
        ok_(self.task.date_done is not None,
            'Resolving task should set date_done')
        ok_(self.task.resolved_by is None,
            'Resolving without providing a user should leave the field blank.')

    def test_resolve_with_user(self):
        """Tasks should record the user responsible for the resolution."""
        user = factories.UserFactory()
        self.task.resolve(user)
        eq_(self.task.resolved_by, user,
            'The resolving user should be recorded by the task.')


class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    def setUp(self):
        self.comm = factories.FOIACommunicationFactory()
        self.task = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='Whatever Who Cares')

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Orphan tasks given reason and communication arguments should create successfully')

    def test_move(self):
        """Should move the communication to the listed requests and create a ResponseTask for each new communication."""
        foia1 = factories.FOIARequestFactory()
        foia2 = factories.FOIARequestFactory()
        foia3 = factories.FOIARequestFactory()
        count_response_tasks = task.models.ResponseTask.objects.count()
        self.task.move([foia1.pk, foia2.pk, foia3.pk])
        eq_(task.models.ResponseTask.objects.count(), count_response_tasks + 3,
            'Reponse tasks should be created for each communication moved.')

    def test_get_sender_domain(self):
        """Should return the domain of the orphan's sender."""
        eq_(self.task.get_sender_domain(), 'muckrock.com')

    def test_reject(self):
        """Shouldn't do anything, ATM. Revisit later."""
        self.task.reject()

    def test_blacklist(self):
        """A blacklisted orphan should add its sender's domain to the blacklist"""
        self.task.blacklist()
        ok_(task.models.BlacklistDomain.objects.filter(domain='muckrock.com'))

    def test_blacklist_duplicate(self):
        """The blacklist method should not crash when a domain is dupliacted."""
        task.models.BlacklistDomain.objects.create(domain='muckrock.com')
        task.models.BlacklistDomain.objects.create(domain='muckrock.com')
        self.task.blacklist()
        ok_(task.models.BlacklistDomain.objects.filter(domain='muckrock.com'))

    def test_resolve_after_blacklisting(self):
        """After blacklisting, other orphan tasks from the sender should be resolved."""
        other_task = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='Whatever Who Cares')
        self.task.blacklist()
        self.task.refresh_from_db()
        other_task.refresh_from_db()
        ok_(self.task.resolved and other_task.resolved)

    def test_create_blacklist_sender(self):
        """An orphan created from a blacklisted sender should be automatically resolved."""
        self.task.blacklist()
        self.task.refresh_from_db()
        ok_(self.task.resolved)
        new_orphan = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='orphan-address'
        )
        # manually call the method since the signal isn't triggering during testing
        domain_blacklist(task.models.OrphanTask, new_orphan, True)
        new_orphan.refresh_from_db()
        logging.debug(new_orphan.resolved)
        ok_(new_orphan.resolved)


class SnailMailTaskTests(TestCase):
    """Test the SnailMailTask class"""

    def setUp(self):
        self.comm = factories.FOIACommunicationFactory()
        self.task = task.models.SnailMailTask.objects.create(
            category='a',
            communication=self.comm)

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Snail mail tasks should create successfully given a category and a communication')

    def test_set_status(self):
        new_status = 'ack'
        self.task.set_status(new_status)
        eq_(self.task.communication.status, new_status,
            'Setting status should update status of associated communication')
        eq_(self.task.communication.foia.status, new_status,
            'Setting status should update status of associated communication\'s foia request')

    def test_update_date(self):
        old_date = self.task.communication.date
        self.task.update_date()
        ok_(self.task.communication.date > old_date,
            'Date should be moved foward.')
        eq_(self.task.communication.date.day, datetime.now().day,
            'Should update the date to today.')

class NewAgencyTaskTests(TestCase):
    """Test the NewAgencyTask class"""

    def setUp(self):
        self.user = factories.UserFactory()
        self.agency = factories.AgencyFactory(status='pending')
        self.task = task.models.NewAgencyTask.objects.create(
            user=self.user,
            agency=self.agency)

    def test_task_creates_successfully(self):
        ok_(self.task,
            'New agency tasks should create successfully given a user and an agency')

    def test_approve(self):
        self.task.approve()
        eq_(self.task.agency.status, 'approved',
            'Approving a new agency should actually, you know, approve the agency.')

    def test_reject(self):
        replacement = factories.AgencyFactory()
        existing_foia = factories.FOIARequestFactory(agency=self.agency)
        self.task.reject(replacement)
        existing_foia.refresh_from_db()
        eq_(self.task.agency.status, 'rejected',
            'Rejecting a new agency should leave it unapproved.')
        eq_(existing_foia.agency, replacement,
            'The replacement agency should receive the rejected agency\'s requests.')

class ResponseTaskTests(TestCase):
    """Test the ResponseTask class"""

    def setUp(self):
        comm = factories.FOIACommunicationFactory(response=True)
        self.task = task.models.ResponseTask.objects.create(communication=comm)

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Response tasks should creates successfully given a communication')

    def test_set_status_to_ack(self):
        self.task.set_status('ack')
        eq_(self.task.communication.foia.date_done, None,
            'The FOIA should not be set to done if the status does not indicate it is done.')
        eq_(self.task.communication.status, 'ack',
            'The communication should be set to the proper status.')
        eq_(self.task.communication.foia.status, 'ack',
            'The FOIA should be set to the proper status.')

    def test_set_status_to_done(self):
        self.task.set_status('done')
        eq_(self.task.communication.foia.date_done is None, False,
            'The FOIA should be set to done if the status indicates it is done.')
        eq_(self.task.communication.status, 'done',
            'The communication should be set to the proper status.')
        eq_(self.task.communication.foia.status, 'done',
            'The FOIA should be set to the proper status.')

    def test_set_tracking_id(self):
        new_tracking = u'dogs-r-cool'
        self.task.set_tracking_id(new_tracking)
        eq_(self.task.communication.foia.tracking_id, new_tracking,
            'Should update the tracking number on the request.')

    def test_set_date_estimate(self):
        new_date = datetime.now()
        self.task.set_date_estimate(new_date)
        eq_(self.task.communication.foia.date_estimate, new_date,
            'Should update the estimated completion date on the request.')

    def test_set_price(self):
        price = 1.23
        self.task.set_price(price)
        eq_(self.task.communication.foia.price, price,
            'Should update the price on the request.')

    def test_move(self):
        move_to_foia = factories.FOIARequestFactory()
        self.task.move(move_to_foia.id)
        eq_(self.task.communication.foia, move_to_foia,
            'Should move the communication to a different request.')

    @raises(ValueError)
    def test_bad_status(self):
        """Should raise an error if given a nonexistant status."""
        self.task.set_status('foo')

    @raises(ValueError)
    def test_bad_tracking_number(self):
        """Should raise an error if not given a string."""
        self.task.set_tracking_id(['foo'])

    @raises(Http404)
    def test_bad_move(self):
        """Should raise a 404 if non-existant move destination."""
        self.task.move(111111)

    @raises(ValueError)
    def test_bad_price(self):
        """Should raise an error if not given a value convertable to a float"""
        self.task.set_price(1)
        self.task.set_price('1')
        self.task.set_price('foo')


class TestTaskManager(TestCase):
    """Tests for a helpful and handy task object manager."""

    def setUp(self):
        user = factories.UserFactory()
        agency = factories.AgencyFactory(status='pending')
        self.foia = factories.FOIARequestFactory(user=user, agency=agency)
        self.comm = factories.FOIACommunicationFactory(foia=self.foia, response=True)

        # tasks that incorporate FOIAs are:
        # ResponseTask, SnailMailTask, FailedFaxTask, RejectedEmailTask, FlaggedTask,
        # StatusChangeTask, PaymentTask, NewAgencyTask
        response_task = task.models.ResponseTask.objects.create(
            communication=self.comm
        )
        snail_mail_task = task.models.SnailMailTask.objects.create(
            category='a',
            communication=self.comm
        )
        failed_fax_task = task.models.FailedFaxTask.objects.create(
            communication=self.comm
        )
        rejected_email_task = task.models.RejectedEmailTask.objects.create(
            category='d',
            foia=self.foia
        )
        flagged_task = task.models.FlaggedTask.objects.create(
            user=user,
            text='Halp',
            foia=self.foia
        )
        status_change_task = task.models.StatusChangeTask.objects.create(
            user=user,
            old_status='ack',
            foia=self.foia
        )
        payment_task = task.models.PaymentTask.objects.create(
            amount=100.00,
            user=user,
            foia=self.foia
        )
        new_agency_task = task.models.NewAgencyTask.objects.create(
            user=user,
            agency=agency
        )
        self.tasks = [
            response_task,
            snail_mail_task,
            failed_fax_task,
            rejected_email_task,
            flagged_task,
            status_change_task,
            payment_task,
            new_agency_task
        ]

    def test_tasks_for_foia(self):
        """
        The task manager should return all tasks that explictly
        or implicitly reference the provided FOIA.
        """
        returned_tasks = task.models.Task.objects.filter_by_foia(self.foia)
        logging.debug(returned_tasks)
        logging.debug(self.tasks)
        eq_(returned_tasks, self.tasks,
            'The manager should return all the tasks that incorporate this FOIA.')
