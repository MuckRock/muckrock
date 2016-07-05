"""
Models for the project application.
"""

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.task.models import ProjectReviewTask

import taggit


class ProjectQuerySet(models.QuerySet):
    """Object manager for projects"""
    def get_public(self):
        """Only return nonprivate projects"""
        return self.filter(private=False, approved=True)

    def get_pending(self):
        """Only return projects pending approval"""
        return self.filter(private=False, approved=False)

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
            projects = projects.filter(
                models.Q(private=False, approved=True)|
                models.Q(contributors=user)
            ).distinct()
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
        default=True,
        help_text='If a project is private, it is only visible to its contributors.')
    approved = models.BooleanField(
        default=False,
        help_text='If a project is approved, is is visible to everyone.')
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
    crowdfunds = models.ManyToManyField(
        'crowdfund.Crowdfund',
        through='ProjectCrowdfunds',
        related_name='projects'
        )

    tags = taggit.managers.TaggableManager(through='tags.TaggedItemBase', blank=True)
    newsletter = models.CharField(max_length=255, blank=True, help_text='The MailChimp list id.')
    newsletter_label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Newsletter Name',
        help_text='Should describe the newsletter.')
    newsletter_cta = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Newsletter Description',
        help_text='Should encourage readers to subscribe.')


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
        return user in self.contributors.all()

    def editable_by(self, user):
        """Checks whether the user can edit this project."""
        return bool(user.is_staff or self.has_contributor(user))

    def active_crowdfunds(self):
        """Return all the active crowdfunds on this project."""
        return self.crowdfunds.filter(closed=False)

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

    def publish(self, notes):
        """Publishing a project sets it public and returns a ProjectReviewTask."""
        self.make_public()
        return ProjectReviewTask.objects.create(project=self, notes=notes)


class ProjectCrowdfunds(models.Model):
    """Project to Crowdfund through model"""
    # pylint: disable=model-missing-unicode
    project = models.ForeignKey(Project)
    crowdfund = models.OneToOneField('crowdfund.Crowdfund')
