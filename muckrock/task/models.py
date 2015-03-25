"""
Models for the Task application
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.loading import get_model

from datetime import datetime

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class Task(models.Model):
    """A base task model for fields common to all tasks"""

    date_created = models.DateTimeField(auto_now_add=True)
    date_done = models.DateTimeField(blank=True, null=True)
    resolved = models.BooleanField(default=False)
    assigned = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        ordering = ['date_created']

    def __unicode__(self):
        return u'Task: %d' % (self.pk)

    def resolve(self):
        """Resolve the task"""
        self.resolved = True
        self.date_done = datetime.now()
        self.save()

    def assign(self, user):
        """Assign the task"""
        self.assigned = user
        self.save()

class OrphanTask(Task):
    """A communication that needs to be approved before showing it on the site"""
    # pylint: disable=no-member
    reasons = (('bs', 'Bad Sender'),
               ('ib', 'Incoming Blocked'),
               ('ia', 'Invalid Address'))
    reason = models.CharField(max_length=2, choices=reasons)
    communication = models.ForeignKey('foia.FOIACommunication')
    address = models.CharField(max_length=255)

    def __unicode__(self):
        return u'%s: %s' % (self.get_reason_display(), self.communication.foia)

    def move(self, request, foia_pks):
        """Moves the comm and resolves the task"""
        self.communication.move(request, foia_pks)
        self.resolve()

    def reject(self):
        """Simply resolves the request. Should do something to spam addresses."""
        self.resolve()


class SnailMailTask(Task):
    """A communication that needs to be snail mailed"""
    # pylint: disable=no-member
    categories = (('a', 'Appeal'), ('n', 'New'), ('u', 'Update'))
    category = models.CharField(max_length=1, choices=categories)
    communication = models.ForeignKey('foia.FOIACommunication')

    def __unicode__(self):
        return u'%s: %s' % (self.get_category_display(), self.communication.foia)

    def set_status(self, status):
        """Set the status of the comm and FOIA affiliated with this task"""
        comm = self.communication
        foia = comm.foia
        foia.status = status
        foia.update()
        foia.save()
        comm.status = foia.status
        comm.date = datetime.now()
        comm.save()
        self.resolve()


class RejectedEmailTask(Task):
    """A FOIA request has had an outgoing email rejected"""

    categories = (('b', 'Bounced'), ('d', 'Dropped'))
    category = models.CharField(max_length=1, choices=categories)
    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    email = models.EmailField(blank=True)
    error = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return u'%s: %s' % (self.get_category_display(), self.foia)

    def agencies(self):
        """Get the agencies who use this email address"""
        return Agency.objects.filter(Q(email__iexact=self.email) |
                                     Q(other_emails__icontains=self.email))

    def foias(self):
        """Get the FOIAs who use this email address"""
        # to avoid circular dependencies
        # pylint: disable=invalid-name
        FOIARequest = get_model('foia', 'FOIARequest')
        return FOIARequest.objects\
                .filter(Q(email__iexact=self.email) |
                        Q(other_emails__icontains=self.email))\
                .filter(status__in=['ack', 'processed', 'appealing',
                                    'fix', 'payment'])


class StaleAgencyTask(Task):
    """An agency has gone stale"""

    agency = models.ForeignKey(Agency)

    def __unicode__(self):
        return u'Stale Agency: %s' % (self.agency)


class FlaggedTask(Task):
    """A user has flagged a request, agency or jurisdiction"""

    user = models.ForeignKey(User)
    text = models.TextField()

    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    agency = models.ForeignKey(Agency, blank=True, null=True)
    jurisdiction = models.ForeignKey(Jurisdiction, blank=True, null=True)

    def __unicode__(self):
        if self.foia:
            return u'Flagged: %s' % (self.foia)
        if self.agency:
            return u'Flagged: %s' % (self.agency)
        if self.jurisdiction:
            return u'Flagged: %s' % (self.jurisdiction)
        return u'Flagged: <None>'


class NewAgencyTask(Task):
    """A new agency has been created and needs approval"""

    user = models.ForeignKey(User, blank=True, null=True)
    agency = models.ForeignKey(Agency)

    def __unicode__(self):
        return u'New Agency: %s' % (self.agency)

    def approve(self):
        """Approves agency and resolves task"""
        self.agency.approved = True
        self.agency.save()
        self.resolve()

    def reject(self):
        """
        Simply resolves task.
        Should do something to the FOIAs attributed to the rejected agency.
        """
        self.resolve()


class ResponseTask(Task):
    """A response has been received and needs its status set"""
    # pylint: disable=no-member
    communication = models.ForeignKey('foia.FOIACommunication')

    def __unicode__(self):
        return u'Response: %s' % (self.communication.foia)

    def set_status(self, status):
        """Sets status of comm and foia; resolves task"""
        comm = self.communication
        foia = comm.foia
        foia.status = status
        foia.update()
        if status in ['rejected', 'no_docs', 'done', 'abandoned']:
            foia.date_done = comm.date
        foia.save()
        comm.status = foia.status
        if status in ['ack', 'processed', 'appealing']:
            comm.date = datetime.now()
        comm.save()
        self.resolve()
