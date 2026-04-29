"""Utility functions for the gethelp app"""

from collections import defaultdict

import markdown

from muckrock.gethelp.models import Problem


def _serialize_problem(problem, children_by_parent):
    """Serialize a single problem and its children recursively"""
    children = children_by_parent.get(problem.pk, [])
    return {
        "id": problem.pk,
        "title": problem.title,
        "resolution_html": (
            markdown.markdown(problem.resolution) if problem.resolution else ""
        ),
        "flag_category": problem.flag_category,
        "children": [
            _serialize_problem(child, children_by_parent) for child in children
        ],
    }


def get_problems_by_category():
    """Serialize all problems as a nested structure grouped by category.

    Returns a dict keyed by category slug with label and nested problems.
    """
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

    return result
