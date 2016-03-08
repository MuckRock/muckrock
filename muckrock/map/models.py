"""
Models for the Map application
"""

from django.db import models
from django.utils.text import slugify

from djgeojson.fields import PointField

DEFAULT_CENTER_POINT = {"type": "Point", "coordinates": [39.83, -98.58]}
DEFAULT_ZOOM_LEVEL = 4

class Map(models.Model):
    """A map holds a collection of Markers."""
    title = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    private = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    center = PointField(default=DEFAULT_CENTER_POINT)
    zoom = models.IntegerField(default=DEFAULT_ZOOM_LEVEL)
    project = models.ForeignKey(
        'project.Project',
        on_delete=models.CASCADE,
        related_name='maps',
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Map, self).save(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.title)

class Marker(models.Model):
    """A Marker connects a FOIARequest to a Map with a location."""
    map = models.ForeignKey(
        Map,
        on_delete=models.CASCADE,
        related_name='markers'
    )
    foia = models.ForeignKey(
        'foia.FOIARequest',
        on_delete=models.CASCADE,
        related_name='locations'
    )
    point = PointField(blank=True)

    def __unicode__(self):
        return u'Marker on %s' % map
