"""Tests for the gethelp models"""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from muckrock.gethelp.models import Problem


@pytest.mark.django_db
class TestProblem(TestCase):
    """Tests for the Problem model"""

    def test_create_problem(self):
        """A problem can be created with all fields"""
        problem = Problem.objects.create(
            category="managing",
            title="The agency is non-responsive",
            resolution="## Steps\n\nFollow up with the agency.",
            flag_category="no response",
            order=0,
        )
        assert problem.pk is not None
        assert problem.category == "managing"
        assert problem.title == "The agency is non-responsive"
        assert problem.resolution == "## Steps\n\nFollow up with the agency."
        assert problem.flag_category == "no response"

    def test_str(self):
        """__str__ returns the title"""
        problem = Problem.objects.create(
            category="managing",
            title="Test problem",
        )
        assert str(problem) == "Test problem"

    def test_category_choices(self):
        """Only valid category values are accepted during full_clean"""
        problem = Problem(
            category="invalid_category",
            title="Bad category",
        )
        with self.assertRaises(ValidationError):
            problem.full_clean()

    def test_valid_categories(self):
        """All defined categories are accepted"""
        valid_categories = [
            "managing",
            "communications",
            "payments",
            "documents",
            "portals",
            "appeals",
            "proxy",
        ]
        for cat in valid_categories:
            problem = Problem(category=cat, title=f"Test {cat}")
            problem.full_clean()  # should not raise

    def test_self_referential_parent(self):
        """A problem can have a parent problem"""
        parent = Problem.objects.create(
            category="managing",
            title="Parent problem",
        )
        child = Problem.objects.create(
            category="managing",
            title="Child problem",
            parent=parent,
        )
        assert child.parent == parent
        assert list(parent.children.all()) == [child]

    def test_nested_children(self):
        """Problems can nest multiple levels deep"""
        grandparent = Problem.objects.create(
            category="managing",
            title="Grandparent",
        )
        parent = Problem.objects.create(
            category="managing",
            title="Parent",
            parent=grandparent,
        )
        child = Problem.objects.create(
            category="managing",
            title="Child",
            parent=parent,
        )
        assert child.parent == parent
        assert parent.parent == grandparent
        assert list(parent.children.all()) == [child]

    def test_cascade_delete(self):
        """Deleting a parent deletes its children"""
        parent = Problem.objects.create(
            category="managing",
            title="Parent",
        )
        Problem.objects.create(
            category="managing",
            title="Child",
            parent=parent,
        )
        assert Problem.objects.count() == 2
        parent.delete()
        assert Problem.objects.count() == 0

    def test_ordering(self):
        """Problems are ordered by category then order"""
        p3 = Problem.objects.create(category="communications", title="Comms 1", order=0)
        p1 = Problem.objects.create(category="managing", title="Managing 2", order=1)
        p2 = Problem.objects.create(category="managing", title="Managing 1", order=0)
        problems = list(Problem.objects.all())
        # "communications" < "managing" alphabetically, then by order
        assert problems == [p3, p2, p1]

    def test_blank_resolution(self):
        """Resolution can be blank"""
        problem = Problem.objects.create(
            category="managing",
            title="No resolution",
            resolution="",
        )
        problem.full_clean()  # should not raise

    def test_blank_flag_category(self):
        """flag_category can be blank"""
        problem = Problem.objects.create(
            category="managing",
            title="No flag mapping",
            flag_category="",
        )
        problem.full_clean()  # should not raise

    def test_null_parent(self):
        """Top-level problems have null parent"""
        problem = Problem.objects.create(
            category="managing",
            title="Top level",
        )
        assert problem.parent is None
