"""Tests for the gethelp admin"""

# Django
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase

# Third Party
import pytest

# MuckRock
from muckrock.gethelp.admin import ProblemAdmin
from muckrock.gethelp.models import Problem


@pytest.mark.django_db
class TestProblemAdmin(TestCase):
    """Tests for the Problem admin configuration"""

    def test_problem_registered(self):
        """Problem model is registered in the admin site"""
        assert admin.site.is_registered(Problem)

    def test_admin_list_display(self):
        """Admin list_display is configured"""
        admin_instance = ProblemAdmin(Problem, AdminSite())
        assert "title" in admin_instance.list_display
        assert "category" in admin_instance.list_display
        assert "order" in admin_instance.list_display

    def test_admin_list_filter(self):
        """Admin list_filter includes category"""
        admin_instance = ProblemAdmin(Problem, AdminSite())
        assert "category" in admin_instance.list_filter

    def test_admin_search_fields(self):
        """Admin search_fields includes title"""
        admin_instance = ProblemAdmin(Problem, AdminSite())
        assert "title" in admin_instance.search_fields

    def test_admin_has_inlines(self):
        """Admin has inline for child problems"""
        admin_instance = ProblemAdmin(Problem, AdminSite())
        assert len(admin_instance.inlines) > 0
        inline_cls = admin_instance.inlines[0]
        assert inline_cls.model is Problem
