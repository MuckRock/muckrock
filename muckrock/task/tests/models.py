"""
Tests for Tasks models
"""

from django.contrib.auth.models import User
from django.test import TestCase

from datetime import datetime
from mock import Mock
import nose.tools as nose

from muckrock import task
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest

# pylint: disable=missing-docstring

class TaskTests(TestCase):
    """Test the Task base class"""

    fixtures = ['test_users.json']

    def setUp(self):
        self.task = task.models.Task.objects.create()

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Tasks given no arguments should create successfully')

    def test_unicode(self):
        nose.eq_(str(self.task), 'Task: %d' % self.task.pk,
            'Unicode string should return the classname and PK of the task')

    def test_resolve(self):
        self.task.resolve()
        nose.ok_(self.task.resolved is True,
            'Resolving task should set resolved field to True')
        nose.ok_(self.task.date_done is not None,
            'Resolving task should set date_done')

    def test_assign(self):
        user = User.objects.get(pk=1)
        self.task.assign(user)
        nose.ok_(self.task.assigned is user,
            'Should assign the task to the specified user')

class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.comm = FOIACommunication.objects.create(date=datetime.now(), from_who='God')
        self.task = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='Whatever Who Cares')

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Orphan tasks given reason and communication arguments should create successfully')

    def test_move(self):
        self.task.move(Mock(), [1, 2, 3])
        nose.eq_(self.task.resolved, True,
            'Moving an orphan to a foia should mark it as resolved')

    def test_reject(self):
        self.task.reject()
        nose.eq_(self.task.resolved, True,
            'Rejecting an orphan should mark it as resolved')

class SnailMailTaskTests(TestCase):
    """Test the SnailMailTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.foia = FOIARequest.objects.get(pk=1)
        self.comm = FOIACommunication.objects.create(date=datetime.now(), from_who='God', foia=self.foia)
        self.task = task.models.SnailMailTask.objects.create(
            category='a',
            communication=self.comm)

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Snail mail tasks should create successfully given a category and a communication')

    def test_set_status(self):
        self.task.set_status('ack')
        nose.eq_(self.task.communication.status, 'ack',
            'Setting status should update status of associated communication')
        nose.eq_(self.task.communication.foia.status, 'ack',
            'Setting status should update status of associated communication\'s foia request')
        nose.eq_(self.task.resolved, True,
            'Setting status should resolve the task')

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
        nose.ok_(self.task,
            'New agency tasks should create successfully given a user and an agency')

    def test_approve(self):
        self.task.approve()
        nose.eq_(self.task.agency.approved, True,
            'Approving a new agency should actually, you know, approve the agency.')
        nose.eq_(self.task.resolved, True,
            'Approving a new agency should resolve the task.')

    def test_reject(self):
        self.task.reject()
        nose.eq_(self.task.agency.approved, False,
            'Rejecting a new agency should not approve it.')
        nose.eq_(self.task.resolved, True,
            'Rejecting a new agency should resolve the task.')

class ResponseTaskTests(TestCase):
    """Test the ResponseTask class"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json']

    def setUp(self):
        self.foia = FOIARequest.objects.get(pk=1)
        self.comm = FOIACommunication.objects.create(date=datetime.now(), from_who='God', foia=self.foia)
        self.task = task.models.ResponseTask.objects.create(
            communication=self.comm)

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Response tasks should creates successfully given a communication')

    def test_set_status_to_ack(self):
        self.task.set_status('ack')
        nose.eq_(self.task.communication.foia.date_done, None,
            'The FOIA should not be set to done if the status does not indicate it is done.')
        nose.eq_(self.task.communication.status, 'ack',
            'The communication should be set to the proper status.')
        nose.eq_(self.task.communication.foia.status, 'ack',
            'The FOIA should be set to the proper status.')
        nose.eq_(self.task.resolved, True,
            'The task should be resolved after setting the status.')

    def test_set_status_to_done(self):
        self.task.set_status('done')
        nose.eq_(self.task.communication.foia.date_done is None, False,
            'The FOIA should be set to done if the status indicates it is done.')
        nose.eq_(self.task.communication.status, 'done',
            'The communication should be set to the proper status.')
        nose.eq_(self.task.communication.foia.status, 'done',
            'The FOIA should be set to the proper status.')
        nose.eq_(self.task.resolved, True,
            'The task should be resolved after setting the status.')
