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
        self.tag_foo = models.Tag.objects.create(name=u'foo')
        self.tag_bar = models.Tag.objects.create(name=u'bar')
        self.tag_baz = models.Tag.objects.create(name=u'baz')

    def test_resolve_url(self):
        """The tag list url should resolve."""
        tag_url = reverse('tag-list')
        response = self.client.get(tag_url)
        eq_(response.status_code, 200)

    def test_list_all_tags(self):
        """The tag list should list all the tags (duh!)."""
        # pylint: disable=no-self-use
        tag_list = views.list_all_tags()
        eq_(len(tag_list), 3)

    def test_filter_tags(self):
        """The tag list should filter tags against a string."""
        filter_string = 'ba'
        filtered_tag_list = views.filter_tags(filter_string)
        eq_(len(filtered_tag_list), 2)
        ok_(self.tag_bar in filtered_tag_list)
        ok_(self.tag_baz in filtered_tag_list)
