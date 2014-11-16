"""
Models for the organization application
"""

from django.contrib.auth.models import User
from django.db import models

from datetime import datetime

from muckrock.settings import MONTHLY_REQUESTS

class Organization(models.Model):
    """Orginization to allow pooled requests and collaboration"""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    owner = models.ForeignKey(User)
    num_requests = models.IntegerField(default=0)
    date_update = models.DateField()
    stripe_id = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('org-detail', [], {'slug': self.slug})

    def get_requests(self):
        """Get the number of requests left for this month"""

        if self.date_update.month != datetime.now().month or \
                self.date_update.year != datetime.now().year:
            # update requests if they have not yet been updated this month
            self.date_update = datetime.now()
            self.num_requests = MONTHLY_REQUESTS.get('org', 0)
            self.save()

        return self.num_requests
