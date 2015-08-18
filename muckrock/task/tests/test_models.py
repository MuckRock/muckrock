"""
Tests for Tasks models
"""

from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase

from datetime import datetime
import logging
import nose

from muckrock import task
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

# pylint: disable=missing-docstring
# pylint: disable=line-too-long

class TaskTests(TestCase):
    """Test the Task base class"""

    fixtures = ['test_users.json']

    def setUp(self):
        self.task = task.models.Task.objects.create()

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Tasks given no arguments should create successfully')

    def test_unicode(self):
        eq_(str(self.task), 'Task: %d' % self.task.pk,
            'Unicode string should return the classname and PK of the task')

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
        user = User.objects.create(username='test', password='pass')
        self.task.resolve(user)
        eq_(self.task.resolved_by, user,
            'The resolving user should be recorded by the task.')


class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.comm = FOIACommunication.objects.create(
                date=datetime.now(),
                from_who='God',
                full_html=False,
                opened=False,
                response=True)
        self.task = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='Whatever Who Cares')

    def test_task_creates_successfully(self):
        ok_(self.task,
            'Orphan tasks given reason and communication arguments should create successfully')

    def test_move(self):
        """Should move the communication to the listed requests and create a ResponseTask for each new communication."""
        count_response_tasks = task.models.ResponseTask.objects.count()
        self.task.move([1, 2, 3])
        eq_(task.models.ResponseTask.objects.count(), count_response_tasks + 3,
            'Reponse tasks should be created for each communication moved.')

    def test_reject(self):
        """Shouldn't do anything, ATM. Revisit later."""
        self.task.reject()

    def test_blacklist(self):
        """A blacklisted email should be automatically resolved"""
        # pylint: disable=no-self-use
        blacklist_domain = task.models.BlacklistDomain.objects.create(domain='spam.com')
        blacklist_domain.save()
        comm = FOIACommunication.objects.create(
                date=datetime.now(),
                from_who='spammer',
                priv_from_who='evil@spam.com')
        orphan = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=comm,
            address='orphan-address')
        updated_orphan = task.models.OrphanTask.objects.get(pk=orphan.pk)
        nose.tools.ok_(updated_orphan.resolved)

class SnailMailTaskTests(TestCase):
    """Test the SnailMailTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.foia = FOIARequest.objects.get(pk=1)
        self.comm = FOIACommunication.objects.create(
                date=datetime.now(),
                from_who='God',
                foia=self.foia,
                full_html=False,
                opened=False,
                response=True)
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

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.agency = Agency.objects.get(pk=1)
        self.agency.approved = False
        self.task = task.models.NewAgencyTask.objects.create(
            user=self.user,
            agency=self.agency)

    def test_task_creates_successfully(self):
        ok_(self.task,
            'New agency tasks should create successfully given a user and an agency')

    def test_approve(self):
        self.task.approve()
        eq_(self.task.agency.approved, True,
            'Approving a new agency should actually, you know, approve the agency.')

    def test_reject(self):
        replacement = Agency.objects.get(id=2)
        count_new = FOIARequest.objects.filter(agency=self.task.agency).count()
        count_replacement = FOIARequest.objects.filter(agency=replacement).count()
        self.task.reject(replacement)
        logging.debug('Count New: %s', count_new)
        logging.debug('Count Replacement: %s', count_replacement)
        logging.debug('Count Expected: %s', count_new + count_replacement)
        logging.debug('Count Actual: %s', FOIARequest.objects.filter(agency=replacement).count())
        eq_(self.task.agency.approved, False,
            'Rejecting a new agency should not approve it.')
        eq_(
            FOIARequest.objects.filter(agency=replacement).count(),
            count_new + count_replacement,
            'The replacement agency should receive the requests'
        )

class ResponseTaskTests(TestCase):
    """Test the ResponseTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.foia = FOIARequest.objects.get(pk=1)
        self.comm = FOIACommunication.objects.create(
                date=datetime.now(),
                from_who='God',
                foia=self.foia,
                full_html=False,
                opened=False,
                response=True)
        self.task = task.models.ResponseTask.objects.create(communication=self.comm)

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

    def test_set_price(self):
        price = 1.23
        self.task.set_price(price)
        eq_(self.task.communication.foia.price, price,
            'Should update the price on the request.')

    def test_move(self):
        move_to = 2
        self.task.move(2)
        eq_(self.task.communication.foia.id, move_to,
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
