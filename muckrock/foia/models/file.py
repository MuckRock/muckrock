# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

import logging
import os

from muckrock.foia.models.request import FOIARequest
from muckrock.foia.models.communication import FOIACommunication

logger = logging.getLogger(__name__)


class FOIAFile(models.Model):
    """An arbitrary file attached to a FOIA request"""

    access = (('public', 'Public'), ('private', 'Private'), ('organization', 'Organization'))

    foia = models.ForeignKey(FOIARequest, related_name='files', blank=True, null=True)
    comm = models.ForeignKey(FOIACommunication, related_name='files', blank=True, null=True)
    ffile = models.FileField(upload_to='foia_files/%Y/%m/%d', verbose_name='File', max_length=255)
    title = models.CharField(max_length=255)
    date = models.DateTimeField(null=True, db_index=True)
    source = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    # for doc cloud only
    access = models.CharField(max_length=12, default='public', choices=access)
    doc_id = models.SlugField(max_length=80, blank=True, editable=False)
    pages = models.PositiveIntegerField(default=0, editable=False)

    def __unicode__(self):
        return self.title

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    def is_doccloud(self):
        """Is this a file doc cloud can support"""

        _, ext = os.path.splitext(self.ffile.name)
        return ext.lower() in ['.pdf', '.doc', '.docx']

    def get_thumbnail(self):
        """Get the url to the thumbnail image. If document is not public, use a generic fallback."""
        mimetypes = {
            'avi': 'file-video.png',
            'bmp': 'file-image.png',
            'csv': 'file-spreadsheet.png',
            'gif': 'file-image.png',
            'jpg': 'file-image.png',
            'mp3': 'file-audio.png',
            'mpg': 'file-video.png',
            'png': 'file-image.png',
            'ppt': 'file-presentation.png',
            'pptx': 'file-presentation.png',
            'tif': 'file-image.png',
            'wav': 'file-audio.png',
            'xls': 'file-spreadsheet.png',
            'xlsx': 'file-spreadsheet.png',
            'zip': 'file-archive.png',
        }
        if self.is_public() and self.is_doccloud() and self.doc_id:
            index = self.doc_id.index('-')
            num = self.doc_id[0:index]
            name = self.doc_id[index+1:]
            return (
                'https://assets.documentcloud.org/documents/' +
                num + '/pages/' + name + '-p1-small.gif'
            )
        else:
            filename = mimetypes.get(self.get_extension(), 'file-document.png')
            return '%simg/%s' % (settings.STATIC_URL, filename)

    def get_extension(self):
        """Get the file extension"""
        return os.path.splitext(self.name())[1][1:]

    def get_foia(self):
        """Get FOIA - self.foia should be refactored out"""
        if self.foia:
            return self.foia
        if self.comm and self.comm.foia:
            return self.comm.foia

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.access == 'public'

    def is_eml(self):
        """Is this an eml file?"""
        return self.ffile.name.endswith('.eml')

    def anchor(self):
        """Anchor name"""
        return 'file-%d' % self.pk

    def clone(self, new_comm):
        """Clone this file to a new communication"""
        from muckrock.foia.tasks import upload_document_cloud
        access = 'private' if new_comm.foia.embargo else 'public'
        original_id = self.pk
        self.pk = None
        self.foia = new_comm.foia
        self.comm = new_comm
        self.access = access
        self.source = new_comm.get_source()
        # make a copy of the file on the storage backend
        try:
            new_ffile = ContentFile(self.ffile.read())
        except ValueError:
            error_msg = ('FOIAFile #%s has no data in its ffile field. '
                        'It has not been cloned.')
            logger.error(error_msg, original_id)
            return
        new_ffile.name = self.ffile.name
        self.ffile = new_ffile
        self.save()
        upload_document_cloud.apply_async(args=[self.pk, False], countdown=3)

    class Meta:
        # pylint: disable=too-few-public-methods
        verbose_name = 'FOIA Document File'
        ordering = ['date']
        app_label = 'foia'


def attachment_path(instance, filename):
    """Generate path for attachment file"""
    return 'outbound_attachments/%s/%d/%s' % (
            instance.user.username,
            instance.foia.pk,
            filename,
            )


class OutboundAttachment(models.Model):
    """An uploaded file waiting to be sent out"""

    foia = models.ForeignKey(
            'FOIARequest',
            related_name='pending_attachments',
            )
    user = models.ForeignKey(
            'auth.User',
            related_name='pending_attachments',
            )
    ffile = models.FileField(
            upload_to=attachment_path,
            verbose_name='file',
            max_length=255,
            )
    date_time_stamp = models.DateTimeField()
    sent = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Attachment: %s by %s for request %d' % (
                self.ffile.name,
                self.user.username,
                self.foia.pk,
                )

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)
