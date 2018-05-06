"""
Attachment models for the FOIA application

Attachments are files uploaded to be sent out with a request or composer,
before the communication has been created
"""

# Django
from django.db import models

# Standard Library
import os


def attachment_path(instance, filename):
    """Generate path for attachment file"""
    return 'outbound_%s_attachments/%s/%d/%s' % (
        instance.type,
        instance.user.username,
        instance.attached_to.pk,
        filename,
    )


class AttachmentBase(models.Model):
    """Abstract base model for attachments"""
    user = models.ForeignKey(
        'auth.User',
        related_name='pending_%(class)s',
    )
    ffile = models.FileField(
        upload_to=attachment_path,
        verbose_name='file',
        max_length=255,
    )
    date_time_stamp = models.DateTimeField()
    sent = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Attachment: %s by %s for %s %d' % (
            self.ffile.name,
            self.user.username,
            self.type,
            self.attached_to.pk,
        )

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    class Meta:
        abstract = True


class OutboundRequestAttachment(AttachmentBase):
    """An uploaded file waiting to be sent out with a request"""

    foia = models.ForeignKey(
        'FOIARequest',
        related_name='pending_attachments',
    )

    type = 'request'

    @property
    def attached_to(self):
        """Return the request this attachment is attached to"""
        return self.foia


class OutboundComposerAttachment(AttachmentBase):
    """An uploaded file waiting to be sent out"""

    composer = models.ForeignKey(
        'FOIAComposer',
        related_name='pending_attachments',
    )

    type = 'composer'

    @property
    def attached_to(self):
        """Return the composer this attachment is attached to"""
        return self.composer
