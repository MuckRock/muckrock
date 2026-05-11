"""Tests for the gethelp signal handlers"""

# Django
from django.core.cache import cache
from django.test import TestCase, override_settings

# Third Party
import pytest

# MuckRock
from muckrock.gethelp.factories import CategoryFactory, ProblemFactory
from muckrock.gethelp.models import Category, Problem
from muckrock.gethelp.utils import CACHE_KEY, get_problems_by_category


@pytest.mark.django_db
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class TestCacheInvalidationSignals(TestCase):
    """Cache is busted whenever Category or Problem is saved or deleted"""

    def setUp(self):
        self.category = CategoryFactory()
        get_problems_by_category()
        assert cache.get(CACHE_KEY) is not None

    def test_category_save_busts_cache(self):
        self.category.label = "Updated"
        self.category.save()
        assert cache.get(CACHE_KEY) is None

    def test_category_delete_busts_cache(self):
        self.category.delete()
        assert cache.get(CACHE_KEY) is None

    def test_problem_save_busts_cache(self):
        problem = ProblemFactory(category=self.category)
        cache.set(CACHE_KEY, "primed", 60)
        problem.title = "Updated"
        problem.save()
        assert cache.get(CACHE_KEY) is None

    def test_problem_delete_busts_cache(self):
        problem = ProblemFactory(category=self.category)
        cache.set(CACHE_KEY, "primed", 60)
        problem.delete()
        assert cache.get(CACHE_KEY) is None

    def test_bulk_category_delete_busts_cache(self):
        CategoryFactory.create_batch(2)
        cache.set(CACHE_KEY, "primed", 60)
        Category.objects.all().delete()
        assert cache.get(CACHE_KEY) is None

    def test_bulk_problem_delete_busts_cache(self):
        ProblemFactory.create_batch(3, category=self.category)
        cache.set(CACHE_KEY, "primed", 60)
        Problem.objects.all().delete()
        assert cache.get(CACHE_KEY) is None
