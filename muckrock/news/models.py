"""
Models for the News application
"""

# Django
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone

# Third Party
from easy_thumbnails.fields import ThumbnailerImageField
from taggit.managers import TaggableManager

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.tags.models import TaggedItemBase


class ArticleQuerySet(models.QuerySet):
    """Object manager for news articles"""

    # pylint: disable=too-many-public-methods

    def get_published(self):
        """Get all published news articles"""
        return self.filter(publish=True, pub_date__lte=timezone.now())

    def get_drafts(self):
        """Get all draft news articles"""
        return self.filter(publish=False)

    def prefetch_authors(self):
        """Prefetch authors"""
        return self.prefetch_related(
            Prefetch(
                "authors",
                queryset=User.objects.select_related("profile").order_by(
                    "authorship__order"
                ),
            )
        )

    def prefetch_editors(self):
        """Prefetch editors"""
        return self.prefetch_related(
            Prefetch("editors", queryset=User.objects.select_related("profile"))
        )


class Article(models.Model):
    """A news article"""

    pub_date = models.DateTimeField("Publish date", default=timezone.now)
    title = models.CharField(max_length=200)
    kicker = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(
        unique=True, help_text='A "Slug" is a unique URL-friendly title for an object.'
    )
    summary = models.TextField(
        help_text="A single paragraph summary or preview of the article."
    )
    body = models.TextField("Body text")
    authors = models.ManyToManyField(
        User, through="authorship", related_name="authored_articles"
    )
    editors = models.ManyToManyField(User, related_name="edited_articles", blank=True)
    publish = models.BooleanField(
        "Publish on site",
        default=False,
        help_text="Articles do not appear on the site until their publish date.",
    )
    foias = models.ManyToManyField(FOIARequest, related_name="articles", blank=True)
    image = ThumbnailerImageField(
        upload_to="news_images/%Y/%m/%d",
        blank=True,
        null=True,
        resize_source={"size": (2400, 800), "crop": "smart"},
    )
    objects = ArticleQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """The url for this object"""
        pub_date = timezone.localtime(self.pub_date)
        kwargs = {
            "year": pub_date.strftime("%Y"),
            "month": pub_date.strftime("%b").lower(),
            "day": pub_date.strftime("%d"),
            "slug": self.slug,
        }
        return reverse("news-detail", kwargs=kwargs)

    def save(self, *args, **kwargs):
        """Save the news article"""
        # pylint: disable=signature-differs
        # epiceditor likes to stick non breaking spaces in here for some reason
        self.body = self.body.replace("\xa0", " ")
        # invalidate the template cache for the page on a save
        self.clear_cache()
        super(Article, self).save(*args, **kwargs)

    def clear_cache(self):
        """Clear the template cache"""
        if self.pk:
            cache.delete(make_template_fragment_key("article_detail_1", [self.pk]))

    def get_authors_names(self):
        """Get all authors names for a byline"""
        authors = list(
            self.authors.order_by("authorship__order").values_list(
                "profile__full_name", flat=True
            )
        )
        if not authors:
            return ""
        names = ", ".join(a for a in authors[:-1])
        if names:
            names = "{} & {}".format(names, authors[-1])
        else:
            names = authors[-1]
        return names

    get_authors_names.short_description = "Authors"

    class Meta:
        ordering = ["-pub_date"]
        get_latest_by = "pub_date"


class Authorship(models.Model):
    """Through model for article to user M2M"""

    article = models.ForeignKey("Article", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order"]


class Photo(models.Model):
    """A photograph to embed in a news article"""

    image = models.ImageField(upload_to="news_photos/%Y/%m/%d")

    def __str__(self):
        return self.image.name
