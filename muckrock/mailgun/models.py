"""
Models for the mailgun app
"""

from django.db import models

class WhitelistDomain(models.Model):
    """A domain to be whitelisted and always accept emails from them"""
    domain = models.CharField(max_length=255)

    def __unicode__(self):
        return self.domain
