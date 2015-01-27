"""
Models for the Task application
"""
from django.contrib.auth.models import User
from django.db import models

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
        return 'Task: %d' % (self.pk)


class OrphanTask(Task):
    """A communication that needs to be approved before showing it on the site"""

    reasons = (('bs', 'Bad Sender'),
               ('ib', 'Incoming Blocked'),
               ('ia', 'Invalid Address'))
    reason = models.CharField(max_length=2, choices=reasons)
    communication = models.ForeignKey('foia.FOIACommunication')
    address = models.CharField(max_length=255)

    def __unicode__(self):
        return '%s: %s' % (self.get_reason_display(), self.communication.foia)


class SnailMailTask(Task):
    """A communication that needs to be snail mailed"""

    categories = (('a', 'Appeal'), ('n', 'New'), ('u', 'Update'))
    category = models.CharField(max_length=1, choices=categories)
    communication = models.ForeignKey('foia.FOIACommunication')

    def __unicode__(self):
        return '%s: %s' % (self.get_category_display(), self.communication.foia)


class RejectedEmailTask(Task):
    """A FOIA request has had an outgoing email rejected"""

    categories = (('b', 'Bounced'), ('d', 'Dropped'))
    category = models.CharField(max_length=1, choices=categories)
    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    email = models.EmailField(blank=True)
    error = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.get_category_display(), self.foia)

    def agencies(self):
        """Get the agencies who use this email address"""
        return Agency.objects.filter(Q(email__iexact=self.email) |
                                     Q(other_emails__icontains=self.email))

    def foias(self):
        """Get the FOIAs who use this email address"""
        return FOIARequest.objects\
                .filter(Q(email__iexact=recipient) |
                        Q(other_emails__icontains=recipient))\
                .filter(status__in=['ack', 'processed', 'appealing',
                                    'fix', 'payment'])


class StaleAgencyTask(Task):
    """An agency has gone stale"""

    agency = models.ForeignKey(Agency)

    def __unicode__(self):
        return 'Stale Agency: %s' % (self.agency)


class FlaggedTask(Task):
    """A user has flagged a request, agency or jurisdiction"""

    user = models.ForeignKey(User)
    text = models.TextField()

    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    agency = models.ForeignKey(Agency, blank=True, null=True)
    jurisdiction = models.ForeignKey(Jurisdiction, blank=True, null=True)

    def __unicode__(self):
        if self.foia:
            return 'Flagged: %s' % (self.foia)
        if self.agency:
            return 'Flagged: %s' % (self.agency)
        if self.jurisdiction:
            return 'Flagged: %s' % (self.jurisdiction)
        return 'Flagged: <None>'


class NewAgencyTask(Task):
    """A new agency has been created and needs approval"""

    user = models.ForeignKey(User, blank=True, null=True)
    agency = models.ForeignKey(Agency)

    def __unicode__(self):
        return 'New Agency: %s' % (self.agency)


class ResponseTask(Task):
    """A response has been received and needs its status set"""

    communication = models.ForeignKey('foia.FOIACommunication')

    def __unicode__(self):
        return 'Response: %s' % (self.communication.foia)
