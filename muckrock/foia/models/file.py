# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

# Django
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction

# Standard Library
import logging
import os

# MuckRock
from muckrock.foia.querysets import FOIAFileQuerySet
from muckrock.foia.utils import file_name_trim

logger = logging.getLogger(__name__)


class FOIAFile(models.Model):
    """An arbitrary file attached to a FOIA request"""

    objects = FOIAFileQuerySet.as_manager()

    comm = models.ForeignKey(
        "foia.FOIACommunication",
        related_name="files",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    ffile = models.FileField(
        upload_to="foia_files/%Y/%m/%d", verbose_name="File", max_length=255
    )
    title = models.CharField(max_length=255)
    datetime = models.DateTimeField(null=True, db_index=True)
    source = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    doc_id = models.SlugField(max_length=266, blank=True, editable=False)
    pages = models.PositiveIntegerField(default=0, editable=False)

    def __str__(self):
        return self.title

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    def is_doccloud(self):
        """Is this a file doc cloud can support"""

        _, ext = os.path.splitext(self.ffile.name)
        return ext.lower() in settings.DOCCLOUD_EXTENSIONS

    def get_thumbnail(self):
        """Get the url to the thumbnail image. If document is not public,
        use a generic fallback."""
        mimetypes = {
            "avi": "file-video.png",
            "csv": "file-spreadsheet.png",
            "mp3": "file-audio.png",
            "mpg": "file-video.png",
            "ppt": "file-presentation.png",
            "pptx": "file-presentation.png",
            "tif": "file-image.png",
            "wav": "file-audio.png",
            "xls": "file-spreadsheet.png",
            "xlsx": "file-spreadsheet.png",
            "zip": "file-archive.png",
        }
        image_preview = ["bmp", "gif", "jpg", "jpeg", "png", "svg", "webp"]
        if self.show_embed:
            id_, slug = self.doc_id.split("-", 1)
            return (
                f"{settings.DOCCLOUD_ASSET_URL}documents/"
                f"{id_}/pages/{slug}-p1-small.gif"
            )
        elif self.get_extension() in image_preview:
            return self.ffile.url
        else:
            filename = mimetypes.get(self.get_extension(), "file-document.png")
            return "%simg/%s" % (settings.STATIC_URL, filename)

    def get_extension(self):
        """Get the file extension"""
        return os.path.splitext(self.name())[1][1:].lower()

    def get_foia(self):
        """Get FOIA"""
        if self.comm and self.comm.foia:
            return self.comm.foia
        else:
            return None

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.access == "public"

    def is_eml(self):
        """Is this an eml file?"""
        return self.ffile.name.endswith(".eml")

    def anchor(self):
        """Anchor name"""
        return "file-%d" % self.pk

    @transaction.atomic
    def clone(self, new_comm):
        """Clone this file to a new communication"""
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.foia.tasks import upload_document_cloud

        original_id = self.pk
        self.pk = None
        self.comm = new_comm
        self.source = new_comm.get_source()
        # make a copy of the file on the storage backend
        try:
            new_ffile = ContentFile(self.ffile.read())
        except ValueError:
            error_msg = (
                "FOIAFile #%s has no data in its ffile field. "
                "It has not been cloned."
            )
            logger.error(error_msg, original_id)
            return
        new_ffile.name = self.name()
        self.ffile = new_ffile
        self.save()
        transaction.on_commit(lambda: upload_document_cloud.delay(self.pk))

    @property
    def access(self):
        """Is this document public or private?"""
        foia = self.get_foia()
        if foia is None:
            return None
        return "organization" if foia.embargo else "public"

    @property
    def show_embed(self):
        """Should we show a DocumentCloud embed for this file?"""
        return (
            self.is_doccloud() and self.doc_id and self.is_public() and self.pages > 0
        )

    class Meta:
        verbose_name = "FOIA Document File"
        ordering = ["datetime"]
        app_label = "foia"


def get_path(file_name):
    """
    Given a file name, get a unique path to a new file on S3

    This is useful to write content directly to S3, then save the path to the DB
    """
    file_name = file_name_trim(file_name)
    file = FOIAFile()
    key = file.ffile.field.generate_filename(file.ffile.instance, file_name)
    return default_storage.get_available_name(key)


# This needs to stick around for migration purposes
def attachment_path(instance, filename):
    """Generate path for attachment file"""
    return "outbound_attachments/%s/%d/%s" % (
        instance.user.username,
        instance.foia.pk,
        filename,
    )
