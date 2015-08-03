"""
Tests for tags
"""
from django import test
from django.core.urlresolvers import reverse

from nose.tools import ok_, eq_

from . import models, views

class TestTagListView(test.TestCase):
    """
    The tag list view should display each tag in a filterable list.
    For each tag in the list, it should display the MuckRock objects
    associated with that tag.
    """

    def setUp(self):
        self.client = test.Client()

    def test_resolve_url(self):
        """The tag list url should resolve."""
        tag_url = reverse('tag-list')
        response = self.client.get(tag_url)
        eq_(response.status_code, 200)

    def test_list_all_tags(self):
        """The tag list should list all the tags (duh!)."""
        # first we create three tag objects
        models.Tag.objects.create(name=u'foo')
        models.Tag.objects.create(name=u'bar')
        models.Tag.objects.create(name=u'baz')
        # next we get a list of all the tags
        tag_list = views.list_all_tags()
        # the list should have three items
        eq_(len(tag_list), 3)
