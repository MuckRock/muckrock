"""
Sidebar Models
"""
from django.db import models
from muckrock.accounts.models import ACCT_TYPES

SIDEBAR_TITLES = ACCT_TYPES + [('anonymous', 'Visitor')]

class SidebarQuerySet(models.QuerySet):
    """Manager for sidebar models"""
    def get_text(self, title):
        """Get the text from the given sidebar if it exists"""
        try:
            sidebar = self.get(title=title)
            return sidebar.text
        except Sidebar.DoesNotExist:
            return None


class Sidebar(models.Model):
    """Text to put into the sidebar"""
    title = models.CharField(max_length=255, unique=True, choices=SIDEBAR_TITLES)
    text = models.TextField(blank=True)

    objects = SidebarQuerySet.as_manager()

    def __unicode__(self):
        return self.title
