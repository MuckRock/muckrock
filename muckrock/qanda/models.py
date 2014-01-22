"""
Models for the Q&A application
"""

from django.contrib.auth.models import User
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string

from taggit.managers import TaggableManager
from urlauth.models import AuthKey

from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.tags.models import TaggedItemBase

class Question(models.Model):
    """A question to which the community can respond"""

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    foia = models.ForeignKey(FOIARequest, blank=True, null=True)
    question = models.TextField(blank=True)
    date = models.DateTimeField()
    answer_date = models.DateTimeField(blank=True, null=True)
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('question-detail', [], {'slug': self.slug, 'idx': self.pk})

    def notify_new(self):
        """Email users who want to be notified of new questions"""
        send_data = []
        for profile in Profile.objects.filter(follow_questions=True):
            link = AuthKey.objects.wrap_url(reverse('question-subscribe'), uid=profile.user.pk)
            msg = render_to_string('qanda/notify.txt', {'question': self, 'link': link})
            send_data.append(('[MuckRock] New FOIA Question: %s' % self, msg,
                              'info@muckrock.com', [profile.user.email]))
        send_mass_mail(send_data, fail_silently=False)

    def notify_update(self):
        """Email users who want to be notified of updates to this question"""
        # pylint: disable=E1101
        send_data = []
        for profile in self.followed_by.all():
            link = AuthKey.objects.wrap_url(reverse('question-follow',
                                                    kwargs={'slug': self.slug, 'idx': self.pk}),
                                            uid=profile.user.pk)
            msg = render_to_string('qanda/follow.txt', {'question': self, 'link': link})
            send_data.append(('[MuckRock] New answer to the question: %s' % self, msg,
                              'info@muckrock.com', [profile.user.email]))
        send_mass_mail(send_data, fail_silently=False)

    class Meta:
        # pylint: disable=R0903
        ordering = ['-date']


class Answer(models.Model):
    """An answer to a proposed question"""

    user = models.ForeignKey(User)
    date = models.DateTimeField()
    question = models.ForeignKey(Question, related_name='answers')
    answer = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        """Update the questions answer date when you save the answer"""
        # pylint: disable=E1101
        super(Answer, self).save(*args, **kwargs)
        question = self.question
        question.answer_date = self.date
        question.save()

    class Meta:
        # pylint: disable=R0903
        ordering = ['date']


