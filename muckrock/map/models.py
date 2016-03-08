"""
Models for the Map application
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from djgeojson.fields import PointField
import json

DEFAULT_CENTER_POINT = json.dumps({
    "type": "Point",
    "coordinates": settings.LEAFLET_CONFIG['DEFAULT_CENTER']
})
DEFAULT_ZOOM_LEVEL = settings.LEAFLET_CONFIG['DEFAULT_ZOOM']

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

    def get_absolute_url(self):
        """Returns the URL for this map"""
        return reverse('map-detail', kwargs={'slug': self.slug, 'idx': self.id})

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

    def save(self, *args, **kwargs):
        """If marker location is empty, try setting it to the location of the FOIA agency."""
        agency_location = self.foia.agency.location if self.foia.agency else ''
        if not self.point and agency_location:
            self.point = self.foia.agency.location
        super(Marker, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'Marker %d on %s' % (self.id, map)
