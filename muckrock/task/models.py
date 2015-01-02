"""
Models for the Task application
"""
from django.db import models


class Task(models.Model):
    """A base task model for fields common to all tasks"""

    date_created = models.DateTimeField(auto_now_add=True)
    date_done = models.DateTimeField(blank=True, null=True)
    resolved = models.BooleanField(default=False)
    assigned = models.ForeignKey(User, blank=True, null=True)


class OrphanTask(Task):
    """A communication that needs to be approved before showing it on the site"""

    task_class = 'orphan'

    reasons = (('bs', 'Bad Sender'), ('ib', 'Incoming Blocked'))
    reason = models.CharField(max_length=2, choices=self.reasons)
    communication = models.ForeignKey(FOIACommunication)


class SnailMailTask(Task):
    """A communication that needs to be snail mailed"""

    task_class = 'snail_mail'

    types = (('a', 'Appeal'), ('n', 'New'), ('u', 'Update'))
    type_ = models.CharField(max_length=1, choices=self.types)
    communication = models.ForeignKey(FOIACommunication)


class RejectedEmailTask(Task):
    """A FOIA request has had an outgoing email rejected"""

    task_class = 'rejected_email'

    types = (('b', 'Bounced'), ('d', 'Dropped'))
    type_ = models.CharField(max_length=1, choices=self.types)
    foia = models.ForeignKey(FOIARequest, blank=True, null=True)
    email = models.EmailField(blank=True)
    error = models.CharField(max_length=255, blank=True)


class StaleAgencyTask(Task):
    """An agency has gone stale"""

    task_class = 'stale_agency'

    agency = models.ForeignKey(Agency)


class FlaggedTask(Task):
    """A user has flagged a request, agency or jurisdiction"""

    task_class = 'flagged'

    user = models.ForeignKey(User)
    text = models.TextField()

    foia = models.ForeignKey(FOIARequest, blank=True, null=True)
    agency = models.ForeignKey(Agency, blank=True, null=True)
    jurisdiction = models.ForeignKey(Jurisdiction, blank=True, null=True)


class NewAgencyTask(Task):
    """A new agency has been created and needs approval"""

    task_class = 'new_agency'

    user = models.ForeignKey(User)
    agency = models.ForeignKey(Agency, blank=True, null=True)


class ResponseTask(Task):
    """A response has been received and needs its status set"""

    task_class = 'response'

    communication = models.ForeignKey(FOIACommunication)
