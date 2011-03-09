"""
Models for the FOIA application
"""

from django.contrib.auth.models import User
from django.db import models

from random import randint

from foia.models import FOIADocument

class Rodeo(models.Model):
    """A Crowd Source manager for a Document Cloud Document"""

    title = models.CharField(max_length=70)
    document = models.ForeignKey(FOIADocument)
    question = models.TextField(blank=True)

    def __unicode__(self):
        # pylint: disable-msg=E1101
        return 'Rodeo for ' + self.document.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable-msg=E1101
        return ('rodeo-detail', [], {'doc_id': self.document.doc_id, 'rodeo_pk': self.pk})

    def random_page(self):
        """Return a random page for the user to vote on"""
        # pylint: disable-msg=E1101
        # do something smarter here to get even votes across pages
        # ensure pages is set
        return randint(1, self.document.pages)

class RodeoOption(models.Model):
    """Options available for someone to choose on a rodeo"""

    title = models.CharField(max_length=70)
    rodeo = models.ForeignKey(Rodeo)

    def __unicode__(self):
        return self.title

class RodeoVote(models.Model):
    """A vote for a rodeo"""

    # need some way of not allowing a user to vote on the same page multiple times

    user = models.ForeignKey(User)
    page = models.IntegerField()
    option = models.ForeignKey(RodeoOption)
