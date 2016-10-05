"""
Models for FOIA Machine
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.utils.text import slugify

from django_hosts.resolvers import reverse

from muckrock.utils import generate_key

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
    sharing_code = models.CharField(max_length=255, blank=True)

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

    def generate_letter(self):
        """Returns a public records request letter for the request's jurisdiction."""
        template = 'text/foia/request.txt'
        context = {
            'jurisdiction': self.jurisdiction,
            'document_request': self.request_language,
            'user_name': self.user.get_full_name()
        }
        return render_to_string(template, context=context).strip()

    def generate_sharing_code(self):
        """Generate a new sharing code, save it to the request, and then return a URL."""
        self.sharing_code = generate_key(12)
        self.save()
        return self.sharing_code


class FoiaMachineCommunication(models.Model):
    """
    A FOIA Machine Communication stores information about an exchange between a user and an agency.
    It is based on the MuckRock existing FOIACommunication object, and also
    loosely mimics the structure of an email.
    """
    request = models.ForeignKey(FoiaMachineRequest, related_name='communications')
    sender = models.CharField(max_length=255)
    receiver = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    date = models.DateField(auto_now_add=True)
    received = models.BooleanField(default=False)

    def __unicode__(self):
        return u'Communication from %s to %s' % (self.sender, self.receiver)

    def get_absolute_url(self):
        return reverse('comm-detail', host='foiamachine', kwargs={
            'foi-slug': self.request.slug,
            'foi-pk': self.request.pk,
            'pk': self.pk,
        })

