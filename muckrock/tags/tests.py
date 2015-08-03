"""
Tests for tags
"""
from django import test
from django.core.urlresolvers import reverse

from nose.tools import ok_

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
        tag_url = reverse('/index')
        response = self.client.get(tag_url)
        ok_(response.status_code == 200)
