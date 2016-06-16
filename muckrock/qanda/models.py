"""
Models for the Q&A application
"""

from django.contrib.auth.models import User
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string

from actstream.models import followers
from sets import Set
from taggit.managers import TaggableManager

from muckrock.foia.models import FOIARequest
from muckrock.tags.models import TaggedItemBase
from muckrock.utils import new_action

class Question(models.Model):
    """A question to which the community can respond"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    foia = models.ForeignKey(FOIARequest, blank=True, null=True)
    question = models.TextField()
    date = models.DateTimeField()
    # We store the date of the most recent answer on the question
    # to increase performance when displaying questions in a list
    # and using the most recent response as a sortable field.
    answer_date = models.DateTimeField(blank=True, null=True)
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Creates an action if question is newly asked"""
        is_new = True if self.pk is None else False
        super(Question, self).save(*args, **kwargs)
        if is_new:
            new_action(self.user, 'asked', target=self)

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('question-detail', [], {'slug': self.slug, 'pk': self.pk})

    def answer_authors(self):
        """Returns a list of users who have answered the question."""
        return [answer.user for answer in self.answers.all()]

    def notify_update(self):
        """Email users who want to be notified of updates to this question"""
        send_data = []
        for user in followers(self):
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
        is_new = True if self.pk is None else False
        super(Answer, self).save(*args, **kwargs)
        self.question.answer_date = self.date
        self.question.save()
        if is_new:
            new_action(self.user, 'answered', action_object=self, target=question)

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['date']
