"""
Tests for tags
"""

# Django
from django import test
from django.urls import reverse

# Third Party
from nose.tools import eq_

# MuckRock
from muckrock.tags import views
from muckrock.tags.models import Tag, normalize


class TestTagModel(test.TestCase):
    """
    Test the normalize function
    """

    def test_convert_to_lowercase(self):
        """The tag should be entirely lowercase"""
        dirty_string = "HELLO"
        expected_clean_string = "hello"
        clean_string = normalize(dirty_string)
        eq_(clean_string, expected_clean_string, "The tag should lowercase its name.")

    def test_strip_whitespace(self):
        """The tag should strip extra whitespace from the beginning and end of
        the name."""
        dirty_string = " hello "
        expected_clean_string = "hello"
        clean_string = normalize(dirty_string)
        eq_(
            clean_string,
            expected_clean_string,
            "The tag should strip extra whitespace from the beginning and end of "
            "the name.",
        )

    def test_collapse_whitespace(self):
        """The tag should remove extra whitespace from between words."""
        dirty_string = "hello    world"
        expected_clean_string = "hello world"
        clean_string = normalize(dirty_string)
        eq_(
            clean_string,
            expected_clean_string,
            "The tag should strip extra whitespace from between words.",
        )


class TestTagListView(test.TestCase):
    """
    The tag list view should display each tag in a filterable list.
    For each tag in the list, it should display the MuckRock objects
    associated with that tag.
    """

    def setUp(self):
        self.client = test.Client()
        self.tag_foo = Tag.objects.create(name="foo")
        self.tag_bar = Tag.objects.create(name="bar")
        self.tag_baz = Tag.objects.create(name="baz")

    def test_resolve_url(self):
        """The tag list url should resolve."""
        tag_url = reverse("tag-list")
        response = self.client.get(tag_url)
        eq_(response.status_code, 200)

    def test_list_all_tags(self):
        """The tag list should list all the tags that are used."""
        tag_list = views.list_all_tags()
        eq_(len(Tag.objects.all()), 3, "There should be 3 tag items.")
        eq_(len(tag_list), 0, "But none should be listed since they aren't used")


class TestTagDetailView(test.TestCase):
    """
    The tag detail view should display the projects, requests, articles and questions
    attached to the current tag.
    """

    def setUp(self):
        self.client = test.Client()
        self.tag_foo = Tag.objects.create(name="foo")

    def test_resolve_url(self):
        """The tag detail url should resolve."""
        tag_url = reverse("tag-detail", kwargs={"slug": self.tag_foo.slug})
        response = self.client.get(tag_url)
        eq_(response.status_code, 200)
