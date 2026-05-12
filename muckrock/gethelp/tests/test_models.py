"""Tests for the gethelp models"""

# Django
from django.core.exceptions import ValidationError
from django.test import TestCase

# Third Party
import pytest

# MuckRock
from muckrock.gethelp.models import Category, Problem


@pytest.mark.django_db
class TestProblem(TestCase):
    """Tests for the Problem model"""

    def setUp(self):
        self.managing = Category.objects.get(slug="managing")

    def test_create_problem(self):
        """A problem can be created with all fields"""
        problem = Problem.objects.create(
            category=self.managing,
            title="The agency is non-responsive",
            resolution="## Steps\n\nFollow up with the agency.",
            flag_category="no response",
            order=0,
        )
        assert problem.pk is not None
        assert problem.category == self.managing
        assert problem.title == "The agency is non-responsive"
        assert problem.resolution == "## Steps\n\nFollow up with the agency."
        assert problem.flag_category == "no response"

    def test_str(self):
        """__str__ returns the title"""
        problem = Problem.objects.create(
            category=self.managing,
            title="Test problem",
        )
        assert str(problem) == "Test problem"

    def test_category_required(self):
        """Problem requires a category FK"""
        problem = Problem(category=None, title="No category")

        with self.assertRaises((ValidationError, Exception)):
            problem.full_clean()

    def test_valid_category(self):
        """A problem can reference any Category object"""
        other = Category.objects.get(slug="payments")
        problem = Problem(category=other, title="Payment issue")
        problem.full_clean()  # should not raise

    def test_self_referential_parent(self):
        """A problem can have a parent problem"""
        parent = Problem.objects.create(
            category=self.managing,
            title="Parent problem",
        )
        child = Problem.objects.create(
            category=self.managing,
            title="Child problem",
            parent=parent,
        )
        assert child.parent == parent
        assert list(parent.children.all()) == [child]

    def test_nested_children(self):
        """Problems can nest multiple levels deep"""
        grandparent = Problem.objects.create(
            category=self.managing,
            title="Grandparent",
        )
        parent = Problem.objects.create(
            category=self.managing,
            title="Parent",
            parent=grandparent,
        )
        child = Problem.objects.create(
            category=self.managing,
            title="Child",
            parent=parent,
        )
        assert child.parent == parent
        assert parent.parent == grandparent
        assert list(parent.children.all()) == [child]

    def test_cascade_delete(self):
        """Deleting a parent deletes its children"""
        parent = Problem.objects.create(
            category=self.managing,
            title="Parent",
        )
        Problem.objects.create(
            category=self.managing,
            title="Child",
            parent=parent,
        )
        assert Problem.objects.count() == 2
        parent.delete()
        assert Problem.objects.count() == 0

    def test_ordering(self):
        """Problems are ordered by category order then problem order"""
        # managing has order=0, communications has order=1 (from migration data)
        communications = Category.objects.get(slug="communications")
        p3 = Problem.objects.create(category=communications, title="Comms 1", order=0)
        p1 = Problem.objects.create(category=self.managing, title="Managing 2", order=1)
        p2 = Problem.objects.create(category=self.managing, title="Managing 1", order=0)
        problems = list(Problem.objects.all())
        # managing (order=0) before communications (order=1), then by problem order
        assert problems == [p2, p1, p3]

    def test_blank_resolution(self):
        """Resolution can be blank"""
        problem = Problem.objects.create(
            category=self.managing,
            title="No resolution",
            resolution="",
        )
        problem.full_clean()  # should not raise

    def test_blank_flag_category(self):
        """flag_category can be blank"""
        problem = Problem.objects.create(
            category=self.managing,
            title="No flag mapping",
            flag_category="",
        )
        problem.full_clean()  # should not raise

    def test_null_parent(self):
        """Top-level problems have null parent"""
        problem = Problem.objects.create(
            category=self.managing,
            title="Top level",
        )
        assert problem.parent is None
