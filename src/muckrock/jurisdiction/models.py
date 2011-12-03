"""
Models for the Jurisdiction application
"""
from django.db import models

class Jurisdiction(models.Model):
    """A jursidiction that you may file FOIA requests in"""

    levels = ( ('f', 'Federal'), ('s', 'State'), ('l', 'Local') )

    name = models.CharField(max_length=50)
    # slug should be slugify(unicode(self))
    slug = models.SlugField(max_length=55)
    abbrev = models.CharField(max_length=5, blank=True)
    level = models.CharField(max_length=1, choices=levels)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True)
    hidden = models.BooleanField(default=False)
    days = models.PositiveSmallIntegerField(blank=True, null=True)

    def __unicode__(self):
        # pylint: disable=E1101
        if self.level == 'l':
            return '%s, %s' % (self.name, self.parent.abbrev)
        else:
            return self.name

    def legal(self):
        """Return the jurisdiction abbreviation for which law this jurisdiction falls under"""
        # pylint: disable=E1101
        if self.level == 'l':
            return self.parent.abbrev
        else:
            return self.abbrev

    def get_days(self):
        """How many days does an agency have to reply?"""
        # pylint: disable=E1101
        if self.level == 'l':
            return self.parent.days
        else:
            return self.days

    class Meta:
        # pylint: disable=R0903
        ordering = ['name']


