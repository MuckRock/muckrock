"""
Models for the Q&A application
"""

from django.contrib.auth.models import User
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string

import actstream
from sets import Set
from taggit.managers import TaggableManager

from muckrock.foia.models import FOIARequest
from muckrock.tags.models import TaggedItemBase


class Question(models.Model):
    """A question to which the community can respond"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    foia = models.ForeignKey(FOIARequest, blank=True, null=True)
    question = models.TextField()
    date = models.DateTimeField()
    answer_date = models.DateTimeField(blank=True, null=True)
    tags = TaggableManager(through=TaggedItemBase, blank=True)
    answer_authors = Set()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Creates an action if question is newly asked"""
        is_new = True if self.pk is None else False
        super(Question, self).save(*args, **kwargs)
        if is_new:
            actstream.action.send(self.user, verb='asked', action_object=self)

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('question-detail', [], {'slug': self.slug, 'pk': self.pk})

    def notify_update(self):
        """Email users who want to be notified of updates to this question"""
        # pylint: disable=no-member
        send_data = []
        for user in actstream.models.followers(self):
            link = user.profile.wrap_url(reverse(
                'question-follow',
                kwargs={'slug': self.slug, 'idx': self.pk}
            ))
            subject = '[MuckRock] New answer to the question: %s' % self
            msg = render_to_string('text/qanda/follow.txt', {'question': self, 'link': link})
            send_data.append((subject, msg, 'info@muckrock.com', [user.email]))
        send_mass_mail(send_data, fail_silently=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['-date']


class Answer(models.Model):
    """An answer to a proposed question"""

    user = models.ForeignKey(User)
    date = models.DateTimeField()
    question = models.ForeignKey(Question, related_name='answers')
    answer = models.TextField()

    reindex_related = ('question',)

    def __unicode__(self):
        return "%s's answer to %s" % (self.user.username, self.question.title)

    def save(self, *args, **kwargs):
        """Update the questions answer date when you save the answer"""
        # pylint: disable=no-member
        is_new = True if self.pk is None else False
        super(Answer, self).save(*args, **kwargs)
        question = self.question
        question.answer_date = self.date
        question.answer_authors.update([self.user])
        question.save()
        if is_new:
            actstream.action.send(self.user, verb='answered', action_object=question)

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['date']
