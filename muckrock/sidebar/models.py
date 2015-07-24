"""
Sidebar Models
"""
from django.db import models
from muckrock.accounts.models import ACCT_TYPES

SIDEBAR_TITLES = ACCT_TYPES + [('anonymous', 'Visitor')]

class Broadcast(models.Model):
    """Text to put into the sidebar"""
    context = models.CharField(max_length=255, unique=True, choices=SIDEBAR_TITLES)
    text = models.TextField(blank=True)

    def __unicode__(self):
        return self.context
