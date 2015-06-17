"""
Models for the project application.
"""

from django.core.urlresolvers import reverse
from django.db import models

import taggit

class Project(models.Model):
    """Projects are a mixture of general and specific information on a broad subject."""
    title = models.CharField(
        unique=True,
        max_length=100,
        help_text='Titles are limited to 100 characters and cannot be changed.')
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    private = models.BooleanField(default=False)
    contributors = models.ManyToManyField(
        'auth.User',
        related_name='projects',
        blank=True,
        null=True)
    articles = models.ManyToManyField(
        'news.Article',
        related_name='projects',
        blank=True,
        null=True)
    requests = models.ManyToManyField(
        'foia.FOIARequest',
        related_name='projects',
        blank=True,
        null=True)
    tags = taggit.managers.TaggableManager(through='tags.TaggedItemBase', blank=True)

    def __unicode__(self):
        return unicode(self.title)

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'slug': self.slug})

    def make_private(self):
        """Sets a project to be private."""
        self.private = True
        self.save()
        return

    def make_public(self):
        """Sets a project to be public."""
        self.private = False
        self.save()
        return
