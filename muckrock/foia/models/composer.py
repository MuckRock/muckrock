"""
Composer model for the FOIA application

This represents a draft request before it is sent.  By selecting multiple
agencies, it is possible to use this to submit a multi-request.  After
submission, the composer stays around to tie together multi-requests and to
serve as the basis for cloning.  This also enables future planned features and
upgrades, such as recurring requests.
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

# Third Party
from taggit.managers import TaggableManager

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.foia.querysets import FOIAComposerQuerySet
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
    status = models.CharField(max_length=10, choices=STATUS, default='started')
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

    objects = FOIAComposerQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    class Meta:
        verbose_name = 'FOIA Composer'
        permissions = (('view_foiacomposer', 'Can view this composer'),)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Set title and slug on save"""
        self.title = self.title.strip() or 'Untitled'
        self.slug = slugify(self.title) or 'untitled'
        super(FOIAComposer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            'foia-composer-detail', kwargs={
                'slug': self.slug,
                'idx': self.pk
            }
        )

    def submit(self):
        """Submit a composer to create the requests"""
        # TODO assuming only the owner can submit
        from muckrock.foia.tasks import approve_composer

        num_requests = self.agencies.count()
        self.user.profile.make_requests(num_requests)
        with transaction.atomic():
            self.status = 'submitted'
            self.datetime_submitted = timezone.now()
            self.save()
            if num_requests < settings.MULTI_REVIEW_AMOUNT:
                # TODO delay actually submitting the request here
                transaction.on_commit(
                    lambda: approve_composer.apply_async(args=(self.pk,))
                )
            else:
                self.multirequesttask_set.create()

    def approved(self):
        """A pending composer is approved for sending to the agencies"""
        for agency in self.agencies.select_related(
            'jurisdiction__law',
            'jurisdiction__parent__law',
        ).iterator():
            FOIARequest.objects.create_new(
                composer=self,
                agency=agency,
            )
        self.status = 'filed'
        self.save()

    def has_perm(self, user, perm):
        """Short cut for checking a FOIA composer permission"""
        return user.has_perm('foia.%s_foiacomposer' % perm, self)
