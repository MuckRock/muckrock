"""
Models for FOIA Machine
"""

from __future__ import unicode_literals

# Django
from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

# Standard Library
from datetime import timedelta

# Third Party
from django_hosts.resolvers import reverse

# MuckRock
from muckrock.foia.models import END_STATUS, STATUS
from muckrock.utils import generate_key


class FoiaMachineRequest(models.Model):
    """
    A FOIA Machine Request stores information about the request.
    It is based on a reconciliation between MuckRock's existing FOIARequest model
    and FOIA Machine's existing Request model.
    """
    user = models.ForeignKey(User)
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default='started',
        db_index=True,
    )
    request_language = models.TextField()
    jurisdiction = models.ForeignKey(
        'jurisdiction.Jurisdiction',
        blank=True,
        null=True,
    )
    agency = models.ForeignKey('agency.Agency', blank=True, null=True)
    sharing_code = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        """Automatically update the slug field."""
        autoslug = kwargs.pop('autoslug', True)
        if autoslug:
            self.slug = slugify(self.title)
        super(FoiaMachineRequest, self).save(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.title)

    def get_absolute_url(self):
        """Returns the request detail url."""
        return reverse(
            'foi-detail',
            host='foiamachine',
            kwargs={
                'slug': self.slug,
                'pk': self.pk,
            }
        )

    def generate_letter(self):
        """Returns a public records request letter for the request's jurisdiction."""
        template = 'text/foia/request.txt'
        context = {
            'jurisdiction': self.jurisdiction,
            'document_request': self.request_language,
            'user_name': self.user.get_full_name()
        }
        return render_to_string(template, context=context).strip()

    def generate_sharing_code(self):
        """Generate a new sharing code, save it to the request, and then return a URL."""
        self.sharing_code = generate_key(12)
        self.save()
        return self.sharing_code

    @property
    def sent_communications(self):
        """Return all communications sent by the user."""
        return self.communications.filter(received=False).order_by('date')

    @property
    def date_submitted(self):
        """The submission date is the date of the first communication."""
        first_comm = self.sent_communications.first()
        if first_comm:
            return first_comm.date
        else:
            raise AttributeError('No communications to track dates on.')

    @property
    def date_due(self):
        """Date due is the date of the last communication plus the jurisdiction response time."""
        last_comm = self.sent_communications.last()
        if self.jurisdiction and self.jurisdiction.days is not None:
            response_time = self.jurisdiction.days
        else:
            response_time = 30
        if last_comm:
            return last_comm.date + timedelta(response_time)
        else:
            raise AttributeError('No communications to track dates on.')

    @property
    def days_until_due(self):
        """Compare the date of the last sent communication to the jurisdiction's response time."""
        try:
            # this subtraction produces a timedelta object, so we need to get the days from it
            days_until_due = self.date_due - timezone.now()
            return days_until_due.days
        except AttributeError:
            return 0

    @property
    def is_overdue(self):
        """A request is overdue if its not completed and days_until_due is negative."""
        return self.status not in END_STATUS and self.days_until_due < 0

    @property
    def days_overdue(self):
        """Days overdue is the inverse of days_until_due."""
        return -1 * self.days_until_due


class FoiaMachineCommunication(models.Model):
    """
    A FOIA Machine Communication stores information about an exchange between a user and an agency.
    It is based on the MuckRock existing FOIACommunication object, and also
    loosely mimics the structure of an email.
    """
    request = models.ForeignKey(
        FoiaMachineRequest, related_name='communications'
    )
    sender = models.CharField(max_length=255)
    receiver = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    received = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Communication from %s to %s' % (self.sender, self.receiver)

    def get_absolute_url(self):
        """Returns the communication detail url."""
        return reverse(
            'comm-detail',
            host='foiamachine',
            kwargs={
                'foi-slug': self.request.slug,
                'foi-pk': self.request.pk,
                'pk': self.pk,
            }
        )


class FoiaMachineFile(models.Model):
    """
    A FOIA Machine File stores files that are created in the course of fulfilling a request.
    Files are uploaded by users and are attached to communications, like in an email.
    """
    communication = models.ForeignKey(
        FoiaMachineCommunication, related_name='files'
    )
    file = models.FileField(
        upload_to='foiamachine_files/%Y/%m/%d',
        verbose_name='File',
        max_length=255,
    )
    name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name
