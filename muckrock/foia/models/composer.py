"""
Composer model for the FOIA application

This represents a draft request before it is sent.  By selecting multiple
agencies, it is possible to use this to submit a multi-request.  After
submission, the composer stays around to tie together multi-requests and to
serve as the basis for cloning.  This also enables future planned features and
upgrades, such as recurring requests.
"""

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Third Party
from taggit.managers import TaggableManager

# MuckRock
from muckrock.tags.models import TaggedItemBase

STATUS = [
    ('started', 'Draft'),
    ('submitted', 'Processing'),
    ('filed', 'Filed'),
]


class FOIAComposer(models.Model):
    """A FOIA request composer"""

    user = models.ForeignKey(User, related_name='composers')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS)
    agencies = models.ManyToManyField('agency.Agency', related_name='composers')
    requested_docs = models.TextField(blank=True)
    datetime_created = models.DateTimeField(default=timezone.now)
    datetime_submitted = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
    )
    embargo = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='The composer this was cloned from, if cloned',
    )

    # for refunding requests if necessary
    num_org_requests = models.PositiveSmallIntegerField(default=0)
    num_monthly_requests = models.PositiveSmallIntegerField(default=0)
    num_reg_requests = models.PositiveSmallIntegerField(default=0)

    tags = TaggableManager(through=TaggedItemBase, blank=True)

    class Meta:
        verbose_name = 'FOIA Composer'

    def __unicode__(self):
        return self.title
