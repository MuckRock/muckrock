# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

from django.contrib.auth.models import User
from django.db import models

from taggit.managers import TaggableManager
import logging

from muckrock.agency.models import Agency
from muckrock.foia.models.request import STATUS
from muckrock.tags.models import TaggedItemBase

logger = logging.getLogger(__name__)

class FOIAMultiRequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS[:2])
    embargo = models.BooleanField(default=False)
    requested_docs = models.TextField(blank=True)
    agencies = models.ManyToManyField(
            Agency,
            related_name='agencies',
            blank=True,
            )

    tags = TaggableManager(through=TaggedItemBase, blank=True)

    foia_type = 'multi'

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('foia-multi-draft', [], {'slug': self.slug, 'idx': self.pk})

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['title']
        verbose_name = 'FOIA Multi-Request'
        app_label = 'foia'
