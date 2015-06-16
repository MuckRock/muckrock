from django.contrib.auth.models import User
from django.db import models

from muckrock.tags.models import TaggedItemBase

from taggit.managers import TaggableManager

class Project(models.Model):
    title = models.CharField(max_length=100, help_text='Titles are limited to 100 characters.')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    private = models.BooleanField(default=False)
    contributors = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
        null=True)
    articles = models.ManyToManyField(
        'news.article',
        related_name='projects',
        blank=True,
        null=True)
    requests = models.ManyToManyField(
        'foia.FOIARequest',
        related_name='projects',
        blank=True,
        null=True)
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        return self.title

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
