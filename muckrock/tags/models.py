"""
Models for the tags application
"""

# pylint: disable=model-missing-unicode

# Django
from django.db import models

# Standard Library
import re

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from taggit.models import Tag as TaggitTag
from taggit.models import GenericTaggedItemBase
from taggit.utils import _parse_tags


def parse_tags(tagstring):
    """Normalize tags after parsing"""
    return [normalize(t) for t in _parse_tags(tagstring)]


def normalize(name):
    """Normalize tag name"""
    clean_name = re.sub(r'\s+', ' ', name)
    return clean_name.strip().lower()[:100]


class Tag(TaggitTag):
    """Custom Tag Class"""

    def save(self, *args, **kwargs):
        """Normalize name before saving"""
        self.name = normalize(self.name)
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name']


class TaggedItemBase(GenericTaggedItemBase):
    """Custom Tagged Item Base Class"""
    tag = models.ForeignKey(Tag, related_name="%(app_label)s_%(class)s_items")


autocomplete_light.register(
    Tag,
    attrs={
        'placeholder': 'Search tags',
        'data-autocomplete-minimum-characters': 1
    }
)
