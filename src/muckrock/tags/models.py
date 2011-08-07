"""
Models for the tags application
"""

from django.contrib.auth.models import User
from django.db import models

from taggit.models import Tag as TaggitTag, GenericTaggedItemBase

class Tag(TaggitTag):
    """Custom Tag Class"""
    user = models.ForeignKey(User, null=True, blank=True)

    def save(self, *args, **kwargs):
        """Normalize name before saving"""
        self.name = Tag.normalize(self.name)
        super(Tag, self).save(*args, **kwargs)

    @staticmethod
    def normalize(name):
        """Normalize tag name"""
        html_remove = dict((ord(c), None) for c in ['<', '>', '&', '"', "'"])
        return name.translate(html_remove).strip().lower()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['name']

class TaggedItemBase(GenericTaggedItemBase):
    """Custom Tagged Item Base Class"""
    tag = models.ForeignKey(Tag, related_name="%(app_label)s_%(class)s_items")

