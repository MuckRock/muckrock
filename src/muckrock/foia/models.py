"""
Models for the FOIA application
"""

from django.db import models
from django.contrib.auth.models import User

JURISDICTIONS = (('MA', 'Massachusetts'),)
JURISDICTIONS_DICT = dict(JURISDICTIONS)

STATUS = (
    ('started', 'Started'),
    ('submitted', 'Submitted'),
    ('fix', 'Fix required'),
    ('rejected', 'Rejected'),
    ('done', 'Response received'),
)
STATUS_DICT = dict(STATUS)

class FOIARequest(models.Model):
    """A Freedom of Information Act request"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=30)
    # tags = ManyToManyField(tags)
    status = models.CharField(max_length=10, choices=STATUS)
    jurisdiction = models.CharField(max_length=5, choices=JURISDICTIONS)
    agency = models.CharField(max_length=30) # choices?
    # fees?
    request = models.TextField()
    response = models.TextField(blank=True)
    # response in pdf/jpg scan of official document version
    date_submitted = models.DateField(blank=True, null=True)
    date_done = models.DateField(blank=True, null=True, verbose_name='Date response received')

    def __unicode__(self):
        return self.title

    def get_status(self):
        """Format the status for output"""
        return STATUS_DICT[self.status]

    def get_jurisdiction(self):
        """Format the jurisdiction for output"""
        return JURISDICTIONS_DICT[self.jurisdiction]

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'


