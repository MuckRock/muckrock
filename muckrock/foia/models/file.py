# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

from django.conf import settings
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
        if self.is_public() and self.is_doccloud():
            index = self.doc_id.index('-')
            num = self.doc_id[0:index]
            name = self.doc_id[index+1:]
            return (
                'https://s3.amazonaws.com/s3.documentcloud.org/documents/' +
                num + '/pages/' + name + '-p1-small.gif'
            )
        else:
            ext = os.path.splitext(self.name())[1][1:]
            filename = mimetypes.get(ext, 'file-document.png')
            return '%simg/%s' % (settings.STATIC_URL, filename)

    def get_foia(self):
        """Get FOIA - self.foia should be refactored out"""
        if self.foia:
            return self.foia
        if self.comm and self.comm.foia:
            return self.comm.foia

    def viewable_by(self, user):
        """Is this document viewable to user"""
        return self.access == 'public' and self.foia.viewable_by(user)

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.access == 'public'

    def is_eml(self):
        """Is this an eml file?"""
        return self.ffile.name.endswith('.eml')

    def anchor(self):
        """Anchor name"""
        return 'file-%d' % self.pk

    class Meta:
        # pylint: disable=too-few-public-methods
        verbose_name = 'FOIA Document File'
        ordering = ['date']
        app_label = 'foia'
