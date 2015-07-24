"""
Models for the project application.
"""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article

import taggit

class Project(models.Model):
    """Projects are a mixture of general and specific information on a broad subject."""
    title = models.CharField(
        unique=True,
        max_length=100,
        help_text='Titles are limited to 100 characters.')
    slug = models.SlugField(
        unique=True,
        max_length=255,
        help_text='The slug is automatically generated based on the title.')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    private = models.BooleanField(
        default=False,
        help_text='If a project is private, it is only visible to its contributors.')
    contributors = models.ManyToManyField(
        'auth.User',
        related_name='projects',
        blank=True,
        )
    articles = models.ManyToManyField(
        'news.Article',
        related_name='projects',
        blank=True,
        )
    requests = models.ManyToManyField(
        'foia.FOIARequest',
        related_name='projects',
        blank=True,
        )
    tags = taggit.managers.TaggableManager(through='tags.TaggedItemBase', blank=True)

    def __unicode__(self):
        return unicode(self.title)

    def save(self, *args, **kwargs):
        """Autogenerates the slug based on the title"""
        self.slug = slugify(self.title)
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Returns the project URL as a string"""
        return reverse('project-detail', kwargs={'pk': self.pk, 'slug': self.slug})

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

    def has_contributor(self, user):
        """Checks if the user is a contributor."""
        if user in self.contributors.all():
            return True
        else:
            return False

    def suggest_requests(self):
        """Returns a list of requests that may be related to this project."""
        requests = list(FOIARequest.objects.filter(
            user__in=self.contributors.all(),
            tags__name__in=self.tags.names()
        ).exclude(projects=self))
        return requests

    def suggest_articles(self):
        """Returns a list of articles that may be related to this project."""
        articles = list(Article.objects.filter(
            authors__in=self.contributors.all(),
            tags__name__in=self.tags.names(),
        ).exclude(projects=self))
        return articles
