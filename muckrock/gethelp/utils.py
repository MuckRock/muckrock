"""Utility functions for the gethelp app"""

from collections import defaultdict

import bleach
import markdown
from django.core.cache import cache

from muckrock.gethelp.models import Problem

CACHE_KEY = "gethelp:problems_by_category"
CACHE_TIMEOUT = 60 * 15  # 15 minutes


def _render_resolution(text):
    """Render markdown to sanitized HTML"""
    if not text:
        return ""
    html = markdown.markdown(text)
    return bleach.clean(
        html,
        tags=["p", "a", "strong", "em", "ul", "ol", "li", "code", "pre", "br", "h1",
              "h2", "h3", "h4", "h5", "h6", "blockquote", "img"],
        attributes={"a": ["href", "title"]},
    )


def _serialize_problem(problem, children_by_parent):
    """Serialize a single problem and its children recursively"""
    children = children_by_parent.get(problem.pk, [])
    return {
        "id": problem.pk,
        "title": problem.title,
        "resolution_html": _render_resolution(problem.resolution),
        "flag_category": problem.flag_category,
        "children": [
            _serialize_problem(child, children_by_parent) for child in children
        ],
    }


def get_problems_by_category():
    """Serialize all problems as a nested structure grouped by category.

    Returns a dict keyed by category slug with label and nested problems.
    Cached for 15 minutes.
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    result = {}
    for key, label in Problem.CATEGORY_CHOICES:
        result[key] = {"label": label, "problems": []}

    problems = list(Problem.objects.order_by("category", "order"))

    # Index children by parent_id
    children_by_parent = defaultdict(list)
    top_level = []
    for problem in problems:
        if problem.parent_id is not None:
            children_by_parent[problem.parent_id].append(problem)
        else:
            top_level.append(problem)

    for problem in top_level:
        serialized = _serialize_problem(problem, children_by_parent)
        result[problem.category]["problems"].append(serialized)

    cache.set(CACHE_KEY, result, CACHE_TIMEOUT)
    return result
