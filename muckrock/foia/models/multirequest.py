# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

# Standard Library
import logging

# Third Party
from taggit.managers import TaggableManager

# MuckRock
from muckrock.tags.models import TaggedItemBase

logger = logging.getLogger(__name__)

STATUS = [
    ('started', 'Draft'),
    ('submitted', 'Processing'),
    ('filed', 'Filed'),
]


class FOIAMultiRequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS)
    embargo = models.BooleanField(default=False)
    requested_docs = models.TextField(blank=True)
    agencies = models.ManyToManyField(
        'agency.Agency',
        related_name='agencies',
        blank=True,
    )
    num_org_requests = models.PositiveSmallIntegerField(default=0)
    num_monthly_requests = models.PositiveSmallIntegerField(default=0)
    num_reg_requests = models.PositiveSmallIntegerField(default=0)
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    tags = TaggableManager(through=TaggedItemBase, blank=True)

    foia_type = 'multi'

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            'foia-multi-detail', kwargs={
                'slug': self.slug,
                'pk': self.pk
            }
        )

    class Meta:
        ordering = ['title']
        verbose_name = 'FOIA Multi-Request'
        app_label = 'foia'
        permissions = ((
            'file_multirequest', 'Can submit requests to multiple agencies'
        ),)
