"""
Models for the tags application
"""

from django.db import models

import autocomplete_light
import re
from taggit.models import Tag as TaggitTag, GenericTaggedItemBase
from taggit.utils import _parse_tags

# pylint: disable=model-missing-unicode

def parse_tags(tagstring):
    """Normalize tags after parsing"""
    return [normalize(t) for t in _parse_tags(tagstring)]

def normalize(name):
    """Normalize tag name"""
    clean_name = re.sub(r'\s+', ' ', name)
    return clean_name.strip().lower()


class Tag(TaggitTag):
    """Custom Tag Class"""

    def save(self, *args, **kwargs):
        """Normalize name before saving"""
        self.name = normalize(self.name)
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['name']

class TaggedItemBase(GenericTaggedItemBase):
    """Custom Tagged Item Base Class"""
    tag = models.ForeignKey(Tag, related_name="%(app_label)s_%(class)s_items")

autocomplete_light.register(Tag)
