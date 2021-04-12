"""
Composer model for the FOIA application

This represents a draft request before it is sent.  By selecting multiple
agencies, it is possible to use this to submit a multi-request.  After
submission, the composer stays around to tie together multi-requests and to
serve as the basis for cloning.  This also enables future planned features and
upgrades, such as recurring requests.
"""

# Django
from celery import current_app
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import F
from django.db.models.functions import Least
from django.db.models.signals import post_delete
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

# Standard Library
from datetime import timedelta
from itertools import zip_longest

# Third Party
from constance import config
from taggit.managers import TaggableManager

# MuckRock
from muckrock.core.utils import TempDisconnectSignal
from muckrock.foia.constants import COMPOSER_EDIT_DELAY, COMPOSER_SUBMIT_DELAY
from muckrock.foia.models.file import FOIAFile
from muckrock.foia.querysets import FOIAComposerQuerySet
from muckrock.tags.models import TaggedItemBase

STATUS = [("started", "Draft"), ("submitted", "Processing"), ("filed", "Filed")]


class FOIAComposer(models.Model):
    """A FOIA request composer"""

    # pylint: disable=too-many-instance-attributes

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="composers")
    # only null for initial migration
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.PROTECT,
        related_name="composers",
        null=True,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS, default="started")
    agencies = models.ManyToManyField("agency.Agency", related_name="composers")
    requested_docs = models.TextField(blank=True)
    edited_boilerplate = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(default=timezone.now, db_index=True)
    datetime_submitted = models.DateTimeField(blank=True, null=True, db_index=True)
    embargo = models.BooleanField(default=False)
    permanent_embargo = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The composer this was cloned from, if cloned",
    )

    # for refunding requests if necessary
    num_monthly_requests = models.PositiveSmallIntegerField(default=0)
    num_reg_requests = models.PositiveSmallIntegerField(default=0)

    # for delayed submission
    delayed_id = models.CharField(blank=True, max_length=255)

    objects = FOIAComposerQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    class Meta:
        verbose_name = "FOIA Composer"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Set title and slug on save"""
        # pylint: disable=signature-differs
        self.title = self.title.strip() or "Untitled"
        self.slug = slugify(self.title) or "untitled"
        super(FOIAComposer, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Resolve any pending new agency tasks"""
        # pylint: disable=signature-differs
        for agency in self.agencies.filter(status="pending"):
            if agency.composers.count() == 1:
                agency.delete()
        super(FOIAComposer, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            "foia-composer-detail", kwargs={"slug": self.slug, "idx": self.pk}
        )

    def submit(self, contact_info=None, no_proxy=False):
        """Submit a composer to create the requests"""
        # pylint: disable=import-outside-toplevel
        from muckrock.foia.tasks import composer_create_foias, composer_delayed_submit

        num_requests = self.agencies.count()
        request_count = self.organization.make_requests(num_requests)
        self.num_reg_requests = request_count["regular"]
        self.num_monthly_requests = request_count["monthly"]
        self.status = "submitted"
        self.datetime_submitted = timezone.now()
        self.save()

        if num_requests == 1:
            # if only one request, create it immediately so we can redirect there
            composer_create_foias(self.pk, contact_info, no_proxy)
        else:
            # otherwise do it delayed so the page doesn't risk timing out
            composer_create_foias.delay(self.pk, contact_info, no_proxy)

        # if num_requests is less than the multi-review amount, we will approve
        # the request right away, other wise we create a multirequest task
        # if the request contains a moderated keyword, it will also not be
        # approved
        approve = (
            num_requests < settings.MULTI_REVIEW_AMOUNT and not self.needs_moderation()
        )
        result = composer_delayed_submit.apply_async(
            args=(self.pk, approve, contact_info), countdown=COMPOSER_SUBMIT_DELAY
        )
        self.delayed_id = result.id
        self.save()

    def needs_moderation(self):
        """Check for moderated keywords"""
        for keyword in config.MODERATION_KEYWORDS.split("\n"):
            if keyword in self.title or keyword in self.requested_docs:
                return True
        return False

    def approved(self, contact_info=None):
        """A pending composer is approved for sending to the agencies"""
        for foia in self.foias.all():
            foia.submit(contact_info=contact_info)
        self.status = "filed"
        self.save()

    def has_perm(self, user, perm):
        """Short cut for checking a FOIA composer permission"""
        return user.has_perm("foia.%s_foiacomposer" % perm, self)

    def return_requests(self, num_requests=None):
        """Return requests to the composer's author"""
        if num_requests is None:
            # if no num_requests passed in, refund all requests
            return_amts = {
                "regular": self.num_reg_requests,
                "monthly": self.num_monthly_requests,
            }
        else:
            return_amts = self._calc_return_requests(num_requests)

        self._return_requests(return_amts)

    @transaction.atomic
    def _return_requests(self, return_amts):
        """Helper method for return requests

        Does the actually returning
        """
        self.num_reg_requests = F("num_reg_requests") - Least(
            return_amts["regular"], F("num_reg_requests")
        )
        self.num_monthly_requests = F("num_monthly_requests") - Least(
            return_amts["monthly"], F("num_monthly_requests")
        )
        self.save()

        self.organization.return_requests(return_amts)

    def _calc_return_requests(self, num_requests):
        """Determine how many of each type of request to return"""
        used = [self.num_reg_requests, self.num_monthly_requests]
        ret = []
        while num_requests:
            try:
                num_used = used.pop(0)
            except IndexError:
                ret.append(num_requests)
                break
            else:
                num_ret = min(num_used, num_requests)
                num_requests -= num_ret
                ret.append(num_ret)
        ret_dict = dict(zip_longest(["regular", "monthly", "extra"], ret, fillvalue=0))
        ret_dict["regular"] += ret_dict.pop("extra")
        return ret_dict

    def revokable(self):
        """Is this composer revokable?"""
        return (
            self.delayed_id != ""
            and self.datetime_submitted
            > timezone.now() - timedelta(seconds=COMPOSER_EDIT_DELAY)
            and self.status == "submitted"
        )

    def revoke(self):
        """Revoke a submitted composer"""
        # pylint: disable=import-outside-toplevel
        from muckrock.foia.signals import foia_file_delete_s3

        current_app.control.revoke(self.delayed_id)
        self.status = "started"
        self.delayed_id = ""
        self.datetime_submitted = None
        disconnect_kwargs = {
            "signal": post_delete,
            "receiver": foia_file_delete_s3,
            "sender": FOIAFile,
            "dispatch_uid": "muckrock.foia.signals.file_delete_s3",
        }
        with TempDisconnectSignal(**disconnect_kwargs):
            self.foias.all().delete()
        self.pending_attachments.update(sent=False)
        self.return_requests()
        self.save()

    def attachments_over_size_limit(self, user):
        """Are the pending attachments for this composer over the size limit?"""
        total_size = sum(
            a.ffile.size for a in self.pending_attachments.filter(user=user, sent=False)
        )
        return total_size > settings.MAX_ATTACHMENT_TOTAL_SIZE
