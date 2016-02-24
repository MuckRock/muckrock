"""
Models for the project application.
"""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article

import taggit


class ProjectQuerySet(models.QuerySet):
    """Object manager for projects"""
    def get_public(self):
        """Only return nonprivate projects"""
        return self.filter(private=False)

    def get_for_contributor(self, user):
        """Only return projects which the user is a contributor on"""
        return self.filter(contributors=user)

    def get_visible(self, user):
        """Only return projects which the user is permitted to see"""
        projects = self.all()
        if not user.is_authenticated():
            # show public projects only
            projects = projects.get_public()
        elif not user.is_staff:
            # show public projects and projects the user is a contributor to
            projects = projects.filter(models.Q(private=False)|models.Q(contributors=user))
            projects = projects.distinct()
        return projects

class Project(models.Model):
    """Projects are a mixture of general and specific information on a broad subject."""
    objects = ProjectQuerySet.as_manager()
    title = models.CharField(
        unique=True,
        max_length=100,
        help_text='Titles are limited to 100 characters.')
    slug = models.SlugField(
        unique=True,
        max_length=255,
        help_text='The slug is automatically generated based on the title.')
    summary = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images/%Y/%m/%d', blank=True, null=True)
    private = models.BooleanField(
        default=False,
        help_text='If a project is private, it is only visible to its contributors.')
    featured = models.BooleanField(
        default=False,
        help_text='Featured projects will appear on the homepage.')
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


class ProjectMap(models.Model):
    """Project maps plot the locations of requests"""
    title = models.CharField(max_length=100, help_text='Titles are limited to 100 characters.')
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, related_name='maps')
    requests = models.ManyToManyField('foia.FOIARequest', related_name='maps', blank=True)

    def __unicode__(self):
        return unicode(self.title)
