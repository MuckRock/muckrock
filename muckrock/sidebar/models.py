"""
Sidebar Models
"""

from django.db import models

SIDEBAR_TITLES = (
   ('article', 'Article'), 
   ('request', 'Request'), 
   ('agency', 'Agency'), 
   ('jurisdiction', 'Jurisdiction'), 
   ('profile', 'Profile'), 
   ('anon_article', 'Anonymous Article'), 
   ('anon_request', 'Anonymous Request'), 
   ('anon_agency', 'Anonymous Agency'), 
   ('anon_jurisdiction', 'Anonymous Jurisdiction'), 
   ('anon_profile', 'Anonymous Profile'), 
)

class SidebarManager(models.Manager):
    """Manager for sidebar models"""
    # pylint: disable=R0904

    def get_text(self, title):
        """Get the text from the given sidebar if it exists"""
        try:
            sidebar = self.get(title=title)
            return sidebar.text
        except Sidebar.DoesNotExist:
            return ''

class Sidebar(models.Model):
    """Text to put into the sidebar"""
    title = models.CharField(max_length=255, unique=True, choices=SIDEBAR_TITLES)
    text = models.TextField(blank=True)

    objects = SidebarManager()
