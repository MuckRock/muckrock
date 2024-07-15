"""
Models for the tags application
"""

# Django
from django.db import models

# Standard Library
import re

# Third Party
from taggit.models import GenericTaggedItemBase, Tag as TaggitTag
from taggit.utils import _parse_tags


def parse_tags(tagstring):
    """Normalize tags after parsing"""
    if not tagstring:
        return []
    elif "," not in tagstring and '"' not in tagstring:
        return [normalize(tagstring)]
    else:
        return [normalize(t) for t in _parse_tags(tagstring)]


def normalize(name):
    """Normalize tag name"""
    clean_name = re.sub(r"\s+", " ", name)
    return clean_name.strip().lower()[:100]


class Tag(TaggitTag):
    """Custom Tag Class"""

    def save(self, *args, **kwargs):
        """Normalize name before saving"""
        self.name = normalize(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["name"]


class TaggedItemBase(GenericTaggedItemBase):
    """Custom Tagged Item Base Class"""

    tag = models.ForeignKey(
        Tag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )
