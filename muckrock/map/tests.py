"""
Tests for the Map application
"""

from django.test import TestCase
from django.utils.text import slugify

import json
from nose.tools import ok_, eq_

from muckrock.factories import FOIARequestFactory, ProjectFactory
from muckrock.map.models import Map, Marker

class UnitTestMap(TestCase):
    """Maps collect markers and belong to projects."""

    def setUp(self):
        self.project = ProjectFactory()
        self.map = Map.objects.create(title='Test map', project=self.project)

    def test_fields(self):
        """
        Maps should contain:
            * a title
            * a slug, based on the title
            * a description, empty by default
            * a privacy flag, lowered by default
            * dates
                * date created
                * date modified
            * view settings
                * center, center of USA by default
                * zoom, 4 by default
            * a collection of Markers, empty by default
            * a project
        """
        ok_(self.map.title,
            'Maps should have a title.')
        eq_(self.map.slug, slugify(self.map.title),
            'The slug should be the slugified title.')
        eq_(self.map.description, '',
            'Maps should have a description that is empty by default.')
        eq_(self.map.private, False,
            'Maps should have a privacy flag lowered by default.')
        ok_(self.map.date_created,
            'Maps should have the date they were created.')
        ok_(self.map.date_updated,
            'Maps should have the date they were last updated.')
        expected_center = json.dumps({
            'type': 'Point',
            'coordinates': [37.8, -96.9]
        })
        eq_(self.map.center, expected_center,
            'Maps should have an initial center point, which is the center of the USA by default.')
        eq_(self.map.zoom, 4,
            'Maps should have an initial zoom level that is 4 by default.')
        eq_(self.map.markers.count(), 0,
            'Maps should have a collection of markers that is empty by default.')
        eq_(self.map.project, self.project,
            'Maps should have a project.')

class UnitTestMarker(TestCase):
    """Markers connect maps, requests, and geo-coordinates."""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.map = Map.objects.create(title='Test map', project=ProjectFactory())
        self.marker = Marker.objects.create(map=self.map, foia=self.foia)

    def test_fields(self):
        """
        Markers should contain:
            * a map
            * a foia
            * a Point location, empty by default
        """
        eq_(self.marker.map, self.map,
            'Markers should be placed on a map.')
        eq_(self.marker.foia, self.foia,
            'Markers should reference a request.')
        eq_(self.marker.point, '',
            'Markers should contain a point location, empty by default.')
