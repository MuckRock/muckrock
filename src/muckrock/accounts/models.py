"""
Models for the accounts application
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField, USStateField

from datetime import datetime

from settings import MONTHLY_REQUESTS

class RequestLimitError(Exception):
    """A user has tried to submit a request when they do not have any left"""

class Profile(models.Model):
    """User profile information for muckrock"""

    user = models.ForeignKey(User, unique=True)
    address1 = models.CharField(max_length=50, blank=True, verbose_name='address')
    address2 = models.CharField(max_length=50, blank=True, verbose_name='address (line 2)')
    city = models.CharField(max_length=60, blank=True)
    state = USStateField(blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    phone = PhoneNumberField(blank=True)

    # for limiting # of requests / month
    monthly_requests = models.IntegerField(default=MONTHLY_REQUESTS)
    date_update = models.DateField()

    def __unicode__(self):
        return u"%s's Profile" % unicode(self.user).capitalize()

    def get_num_requests(self):
        """Get the number of requests left for this month"""
        if self.date_update.month != datetime.now().month or \
                self.date_update.year != datetime.now().year:
            # update requests if they have not yet been updated this month
            self.date_update = datetime.now()
            self.monthly_requests = MONTHLY_REQUESTS
            self.save()

        return self.monthly_requests

    def can_request(self):
        """Predicate for whether or not this user has any requests left"""

        return self.get_num_requests() > 0

    def make_request(self):
        """Reduce one from the user's request amount"""

        if not self.can_request():
            raise RequestLimitError()

        self.monthly_requests -= 1
        self.save()



