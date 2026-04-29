"""Tests for the gethelp utils"""

# Django
from django.core.cache import cache
from django.test import TestCase

# Standard Library
import json

# Third Party
import pytest

# MuckRock
from muckrock.gethelp.models import Problem
from muckrock.gethelp.utils import CACHE_KEY, get_problems_by_category


@pytest.mark.django_db
class TestGetProblemsByCategory(TestCase):
    """Tests for the get_problems_by_category serializer"""

    def setUp(self):
        cache.delete(CACHE_KEY)

    def test_empty_database(self):
        """Returns all categories with empty problem lists when no problems exist"""
        result = get_problems_by_category()
        assert isinstance(result, dict)
        for key, _label in Problem.CATEGORY_CHOICES:
            assert key in result
            assert result[key]["problems"] == []
            assert "label" in result[key]

    def test_is_json_serializable(self):
        """The result can be serialized to JSON"""
        Problem.objects.create(
            category="managing",
            title="Test problem",
            resolution="Some **bold** text",
        )
        result = get_problems_by_category()
        json_str = json.dumps(result)
        assert json_str  # should not raise

    def test_grouped_by_category(self):
        """Problems are grouped under their category key"""
        Problem.objects.create(category="managing", title="Managing problem", order=0)
        Problem.objects.create(category="payments", title="Payment problem", order=0)
        result = get_problems_by_category()
        assert len(result["managing"]["problems"]) == 1
        assert len(result["payments"]["problems"]) == 1
        assert result["managing"]["problems"][0]["title"] == "Managing problem"
        assert result["payments"]["problems"][0]["title"] == "Payment problem"

    def test_category_labels(self):
        """Each category has the correct human-readable label"""
        result = get_problems_by_category()
        assert result["managing"]["label"] == "Managing this request"
        assert result["communications"]["label"] == "Communications and messages"
        assert result["payments"]["label"] == "Checks and request payments"
        assert result["documents"]["label"] == "Documents and files"
        assert result["portals"]["label"] == "Agency portals and web forms"
        assert result["appeals"]["label"] == "Appeals and public records advice"
        assert result["proxy"]["label"] == "In-state proxy and proof of citizenship"

    def test_markdown_rendered_to_html(self):
        """Markdown in resolution is rendered to HTML"""
        Problem.objects.create(
            category="managing",
            title="Test",
            resolution="**bold** and *italic*",
        )
        result = get_problems_by_category()
        problem = result["managing"]["problems"][0]
        assert "<strong>bold</strong>" in problem["resolution_html"]
        assert "<em>italic</em>" in problem["resolution_html"]

    def test_empty_resolution(self):
        """Empty resolution produces empty HTML"""
        Problem.objects.create(
            category="managing",
            title="No resolution",
            resolution="",
        )
        result = get_problems_by_category()
        problem = result["managing"]["problems"][0]
        assert problem["resolution_html"] == ""

    def test_children_nested(self):
        """Child problems are nested under their parent"""
        parent = Problem.objects.create(category="managing", title="Parent", order=0)
        Problem.objects.create(
            category="managing", title="Child", parent=parent, order=0
        )
        result = get_problems_by_category()
        problems = result["managing"]["problems"]
        # Only parent at top level
        assert len(problems) == 1
        assert problems[0]["title"] == "Parent"
        assert len(problems[0]["children"]) == 1
        assert problems[0]["children"][0]["title"] == "Child"

    def test_deeply_nested_children(self):
        """Children can nest multiple levels"""
        grandparent = Problem.objects.create(
            category="managing", title="Grandparent", order=0
        )
        parent = Problem.objects.create(
            category="managing", title="Parent", parent=grandparent, order=0
        )
        Problem.objects.create(
            category="managing", title="Child", parent=parent, order=0
        )
        result = get_problems_by_category()
        problems = result["managing"]["problems"]
        assert len(problems) == 1
        assert problems[0]["title"] == "Grandparent"
        child_of_gp = problems[0]["children"]
        assert len(child_of_gp) == 1
        assert child_of_gp[0]["title"] == "Parent"
        child_of_p = child_of_gp[0]["children"]
        assert len(child_of_p) == 1
        assert child_of_p[0]["title"] == "Child"

    def test_ordering_respected(self):
        """Problems are ordered by their order field"""
        Problem.objects.create(category="managing", title="Second", order=1)
        Problem.objects.create(category="managing", title="First", order=0)
        result = get_problems_by_category()
        problems = result["managing"]["problems"]
        assert problems[0]["title"] == "First"
        assert problems[1]["title"] == "Second"

    def test_flag_category_included(self):
        """flag_category is included in the serialized output"""
        Problem.objects.create(
            category="managing",
            title="Test",
            flag_category="no response",
        )
        result = get_problems_by_category()
        problem = result["managing"]["problems"][0]
        assert problem["flag_category"] == "no response"

    def test_problem_id_included(self):
        """Problem id is included in the serialized output"""
        p = Problem.objects.create(category="managing", title="Test")
        result = get_problems_by_category()
        problem = result["managing"]["problems"][0]
        assert problem["id"] == p.pk

    def test_resolution_html_sanitized(self):
        """Unsafe HTML in resolution is stripped"""
        Problem.objects.create(
            category="managing",
            title="XSS test",
            resolution='<script>alert("xss")</script>**safe**',
        )
        result = get_problems_by_category()
        problem = result["managing"]["problems"][0]
        assert "<script>" not in problem["resolution_html"]
        assert "<strong>safe</strong>" in problem["resolution_html"]
