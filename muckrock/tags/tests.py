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
        """The tag list should list all the tags that are used."""
        # pylint: disable=no-self-use
        tag_list = views.list_all_tags()
        eq_(len(models.Tag.objects.all()), 3,
            "There should be 3 tag items.")
        eq_(len(tag_list), 0,
            "But none should be listed since they aren't used")


class TestTagDetailView(test.TestCase):
    """
    The tag detail view should display the projects, requests, articles and questions
    attached to the current tag.
    """

    def setUp(self):
        self.client = test.Client()
        self.tag_foo = models.Tag.objects.create(name=u'foo')

    def test_resolve_url(self):
        """The tag detail url should resolve."""
        tag_url = reverse('tag-detail', kwargs={'slug': self.tag_foo.slug})
        response = self.client.get(tag_url)
        eq_(response.status_code, 200)

