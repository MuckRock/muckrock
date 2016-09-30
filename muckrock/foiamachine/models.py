"""
Models for FOIA Machine
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from django_hosts.resolvers import reverse

class FoiaMachineRequest(models.Model):
    """
    A FOIA Machine Request stores information about the request.
    It is based on a reconciliation between MuckRock's existing FOIARequest model
    and FOIA Machine's existing Request model.
    """
    user = models.ForeignKey(User)
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255)
    request_language = models.TextField()
    jurisdiction = models.ForeignKey('jurisdiction.Jurisdiction')
    agency = models.ForeignKey('agency.Agency', blank=True, null=True)

    def save(self, *args, **kwargs):
        """Automatically update the slug field."""
        self.slug = slugify(self.title)
        super(FoiaMachineRequest, self).save(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.title)

    def get_absolute_url(self):
        return reverse('foi-detail', host='foiamachine', kwargs={
            'slug': self.slug,
            'pk': self.pk,
        })
