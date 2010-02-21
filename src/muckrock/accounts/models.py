"""
Models for the accounts application
"""

from django.db import models
from django.contrib.auth.models import User
from accounts.states import STATES

class Profile(models.Model):
    """User profile information for muckrock"""

    user = models.ForeignKey(User, unique=True)
    address1 = models.CharField(max_length=50, verbose_name='address')
    address2 = models.CharField(max_length=50, blank=True, verbose_name='address (line 2)')
    city = models.CharField(max_length=60)
    state = models.CharField(max_length=3, choices=STATES)
    zip_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=10)

    def __unicode__(self):
        return u"%s's Profile" % unicode(self.user).capitalize()

