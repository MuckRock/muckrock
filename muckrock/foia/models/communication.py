# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

import datetime

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.validators import validate_email, ValidationError
from django.db import models

import logging

from muckrock.foia.models.request import FOIARequest, STATUS

logger = logging.getLogger(__name__)

DELIVERED = (
    ('fax', 'Fax'),
    ('email', 'Email'),
    ('mail', 'Mail'),
)

class FOIACommunication(models.Model):
    """A single communication of a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='communications', blank=True, null=True)
    from_who = models.CharField(max_length=255)
    to_who = models.CharField(max_length=255, blank=True)
    priv_from_who = models.CharField(max_length=255, blank=True)
    priv_to_who = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(db_index=True)
    response = models.BooleanField(help_text='Is this a response (or a request)?')
    full_html = models.BooleanField()
    communication = models.TextField(blank=True)
    delivered = models.CharField(max_length=10, choices=DELIVERED, blank=True, null=True)
    # what status this communication should set the request to - used for machine learning
    status = models.CharField(max_length=10, choices=STATUS, blank=True, null=True)
    opened = models.BooleanField()

    # only used for orphans
    likely_foia = models.ForeignKey(
        FOIARequest,
        related_name='likely_communications',
        blank=True,
        null=True
    )

    reindex_related = ('foia',)

    def __unicode__(self):
        return '%s: %s...' % (self.date.strftime('%m/%d/%y'), self.communication[:80])

    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable=E1101
        return self.foia.get_absolute_url() + ('#comm-%d' % self.pk)

    def save(self, *args, **kwargs):
        """Remove controls characters from text before saving"""
        remove_control = dict.fromkeys(range(0, 9) + range(11, 13) + range(14, 32))
        self.communication = unicode(self.communication).translate(remove_control)
        # limit communication length to 150k
        self.communication = self.communication[:150000]
        # special handling for certain agencies
        self._presave_special_handling()
        super(FOIACommunication, self).save(*args, **kwargs)

    def anchor(self):
        """Anchor name"""
        return 'comm-%d' % self.pk

    def move(self, foia_pks):
        """Move this communication to all of the FOIAs given by their pk"""
        # avoid circular imports
        from muckrock.foia.tasks import upload_document_cloud
        files = self.files.all()
        foias = []
        # collect the FOIAs
        for foia_pk in foia_pks:
            try:
                foia = FOIARequest.objects.get(pk=foia_pk)
                foias.append(foia)
            except (FOIARequest.DoesNotExist, ValueError):
                logging.error('FOIA %s does not exist', foia_pk)
                continue
        # clone the communication and files to each FOIA
        for foia in foias:
            """
            When setting self.pk to None and then calling self.save(),
            Django will clone the communication along with all of its data
            and give it a new primary key. On the next iteration of the loop,
            the clone will be cloned along with its data, and so on.
            """
            self.pk = None
            self.foia = foia
            self.save()
            for file_ in files:
                file_.pk = None
                file_.foia = new_foia
                file_.comm = self
                # make a copy of the file on the storage backend
                new_ffile = ContentFile(file_.ffile.read())
                new_ffile.name = file_.ffile.name
                file_.ffile = new_ffile
                file_.save()
                upload_document_cloud.apply_async(args=[file_.pk, False], countdown=3)
        if not foias:
            logging.error('No valid FOIA requests given: %s', foia_pks)
            return True
        else:
            msg = 'Communication moved to the following requests: '
            href = lambda f: '<a href="%s">%s</a>' % (f.get_absolute_url(), f.pk)
            msg += ', '.join(href(f) for f in foias)
            logging.info(msg)
            return False

    def resend(self, email=None):
        """Resend the communication"""
        foia = self.foia
        if not foia:
            logging.error('Tried resending an orphaned communication.')
            raise ValueError('This communication has no FOIA to submit.')
        snail = False
        self.date = datetime.datetime.now()
        self.save()
        if email:
            # responsibility for handling validation errors
            # is on the caller of the resend method
            validate_email(email)
            foia.email = email
            foia.save()
        else:
            snail = True
        foia.submit(snail=snail)
        logging.info('Communication %d was resent.', self.id)

    def set_raw_email(self, msg):
        """Set the raw email for this communication"""
        raw_email = RawEmail.objects.get_or_create(communication=self)[0]
        raw_email.raw_email = msg
        raw_email.save()

    def _presave_special_handling(self):
        """Special handling before saving
        For example, strip out BoP excessive quoting"""

        def test_agency_name(name):
            """Match on agency name"""
            return (self.foia and self.foia.agency and
                    self.foia.agency.name == name)

        def until_string(string):
            """Cut communication off after string"""
            def modify():
                """Run the modification on self.communication"""
                if string in self.communication:
                    idx = self.communication.index(string)
                    self.communication = self.communication[:idx]
            return modify

        special_cases = [
            # BoP: strip everything after '>>>'
            (test_agency_name('Bureau of Prisons'),
             until_string('>>>')),
            # Phoneix Police: strip everything after '_'*32
            (test_agency_name('Phoenix Police Department'),
             until_string('_' * 32)),
        ]

        for test, modify in special_cases:
            if test:
                modify()


    class Meta:
        # pylint: disable=R0903
        ordering = ['date']
        verbose_name = 'FOIA Communication'
        app_label = 'foia'


class RawEmail(models.Model):
    """The raw email text for a communication - stored seperately for performance"""

    communication = models.OneToOneField(FOIACommunication)
    raw_email = models.TextField(blank=True)

    def __unicode__(self):
        return 'Raw Email: %d' % self.pk

    class Meta:
        app_label = 'foia'


class FOIANote(models.Model):
    """A private note on a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='notes')
    date = models.DateTimeField()
    note = models.TextField()

    def __unicode__(self):
        # pylint: disable=no-member
        return 'Note for %s on %s' % (self.foia.title, self.date)

    class Meta:
        # pylint: disable=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Note'
        app_label = 'foia'
