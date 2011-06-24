"""
Models for the accounts application
"""

from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField, USStateField
from django.db import models

from datetime import datetime

from foia.models import FOIARequest
from settings import MONTHLY_REQUESTS

class Profile(models.Model):
    """User profile information for muckrock"""

    user = models.ForeignKey(User, unique=True)
    address1 = models.CharField(max_length=50, blank=True, verbose_name='address')
    address2 = models.CharField(max_length=50, blank=True, verbose_name='address (line 2)')
    city = models.CharField(max_length=60, blank=True)
    state = USStateField(blank=True, default='MA')
    zip_code = models.CharField(max_length=10, blank=True)
    phone = PhoneNumberField(blank=True)
    follows = models.ManyToManyField(FOIARequest, related_name='followed_by', blank=True)

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
            return False

        self.monthly_requests -= 1
        self.save()
        return True


class Statistics(models.Model):
    """Nightly statistics"""

    date = models.DateField()

    total_requests = models.IntegerField()
    total_requests_success = models.IntegerField()
    total_requests_denied = models.IntegerField()
    total_pages = models.IntegerField()
    total_users = models.IntegerField()
    users_today = models.ManyToManyField(User)
    total_agencies = models.IntegerField()
    total_fees = models.IntegerField()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['-date']
