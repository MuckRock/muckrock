# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from nose.tools import eq_
from rest_framework.test import APIClient

# MuckRock
from muckrock.core.factories import ProjectFactory


class TestProjectViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project1 = ProjectFactory(title="Project 1", slug="project-1")
        self.project2 = ProjectFactory(title="Project 2", slug="project-2")
        self.project3 = ProjectFactory(title="Project 3", slug="project-3")

    def test_list_projects(self):
        response = self.client.get(reverse("api2-projects-list"))
        eq_(response.status_code, 200)
        results = response.json()["results"]
        eq_(len(results), 3)

    def test_retrieve_project(self):
        response = self.client.get(
            reverse("api2-projects-detail", kwargs={"pk": self.project1.pk})
        )
        eq_(response.status_code, 200)
        eq_(response.json()["id"], self.project1.pk)

    def test_list_projects_filtered(self):
        response = self.client.get(
            reverse("api2-projects-list"), {"id": self.project1.pk}
        )
        eq_(response.status_code, 200)
        results = response.json()["results"]
        eq_(len(results), 1)
        eq_(results[0]["id"], self.project1.pk)

    def test_retrieve_project_not_found(self):
        response = self.client.get(reverse("api2-projects-detail", kwargs={"pk": 9999}))
        eq_(response.status_code, 404)
