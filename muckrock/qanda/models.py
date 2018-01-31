"""
Models for the Q&A application
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

# Third Party
from actstream.models import followers
from taggit.managers import TaggableManager

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.tags.models import TaggedItemBase
from muckrock.utils import new_action, notify


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
            action = new_action(self.user, 'asked', target=self)
            # Notify users who subscribe to new question notifications
            new_question_subscribers = Profile.objects.filter(
                new_question_notifications=True
            )
            users_to_notify = [
                profile.user for profile in new_question_subscribers
            ]
            notify(users_to_notify, action)

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            'question-detail', kwargs={
                'slug': self.slug,
                'pk': self.pk
            }
        )

    def answer_authors(self):
        """Returns a list of users who have answered the question."""
        return (
            User.objects.filter(
                answer__question=self,
                is_active=True,
            ).distinct()
        )

    class Meta:
        ordering = ['-date']
        permissions = (
            ('post', 'Can post questions and answers'),
            ('block', 'Can block other users'),
        )


class Answer(models.Model):
    """An answer to a proposed question"""

    user = models.ForeignKey(User)
    date = models.DateTimeField()
    question = models.ForeignKey(Question, related_name='answers')
    answer = models.TextField()

    reindex_related = ('question',)

    def __unicode__(self):
        return "Answer to %s" % self.question.title

    def get_absolute_url(self):
        """The url for this object"""
        return '%s#answer-%s' % (self.question.get_absolute_url(), self.pk)

    def save(self, *args, **kwargs):
        """Update the questions answer date when you save the answer"""
        is_new = True if self.pk is None else False
        super(Answer, self).save(*args, **kwargs)
        self.question.answer_date = self.date
        self.question.save()
        if is_new:
            action = new_action(
                self.user, 'answered', action_object=self, target=self.question
            )
            # Notify the question's owner and its followers about the new answer
            notify(self.question.user, action)
            notify(followers(self.question), action)

    class Meta:
        ordering = ['date']
