"""
Models for the News application
"""

from django.contrib.auth.models import User
from django.db import models

from datetime import datetime
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager

from foia.models import FOIARequest
from tags.models import TaggedItemBase

class ArticleManager(models.Manager):
    """Object manager for news articles"""
    # pylint: disable=R0904

    def get_published(self):
        """Get all published news articles"""
        return self.filter(publish=True, pub_date__lte=datetime.now)

    def get_drafts(self):
        """Get all draft news articles"""
        return self.filter(publish=False)


class Article(models.Model):
    """A news article"""

    pub_date = models.DateTimeField('Publish date', default=datetime.now)
    title = models.CharField(max_length=200)
    kicker = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(help_text='A "Slug" is a unique URL-friendly title for an object.')
    summary = models.TextField(help_text='A single paragraph summary or preview of the article.')
    body = models.TextField('Body text')
    author = models.ForeignKey(User, limit_choices_to = {'is_staff': True})
    publish = models.BooleanField('Publish on site', default=True,
            help_text='Articles will not appear on the site until their "publish date".')
    foias = models.ManyToManyField(FOIARequest, related_name='articles', blank=True, null=True)
    image = ThumbnailerImageField(upload_to='news_images', blank=True, null=True,
                                  resize_source={'size': (510, 233), 'crop': 'smart'})

    objects = ArticleManager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('news-detail', (), {
                'year': self.pub_date.strftime('%Y'),
                'month': self.pub_date.strftime('%b').lower(),
                'day': self.pub_date.strftime('%d'),
                'slug': self.slug})

    class Meta:
        # pylint: disable=R0903
        ordering = ['-pub_date']
        get_latest_by = 'pub_date'
        unique_together = (('slug', 'pub_date'),)


class Photo(models.Model):
    """A photograph to embed in a news article"""

    image = models.ImageField(upload_to='news_photos')

    def __unicode__(self):
        return self.image.name
