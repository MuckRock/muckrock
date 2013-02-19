"""
Models for the Q&A application
"""

from django.contrib.auth.models import User
from django.db import models

from taggit.managers import TaggableManager

from tags.models import TaggedItemBase

class Question(models.Model):
    """A question to which the community can respond"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    question = models.TextField(blank=True)
    date = models.DateTimeField()
    tags = TaggableManager(through=TaggedItemBase, blank=True)


class Answer(models.Model):
    """An answer to a proposed question"""

    user = models.ForeignKey(User)
    date = models.DateTimeField()
    question = models.ForeignKey(Question, related_name='answers')
    answer = models.TextField(blank=True)
