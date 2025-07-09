# Django
from django.test import Client, TestCase
from django.urls import reverse

# MuckRock
from muckrock.core.factories import ProjectFactory, UserFactory


class TestProjectViewSet(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.project1 = ProjectFactory(title="Project 1", private=False, approved=True)
        self.project2 = ProjectFactory(title="Project 2", private=False, approved=True)
        self.project3 = ProjectFactory(title="Project 3", private=False, approved=True)

        self.list_url = reverse("api2-projects-list")

    def test_list_projects(self):
        response = self.client.get(self.list_url)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 3

    def test_retrieve_project(self):
        response = self.client.get(
            reverse("api2-projects-detail", kwargs={"pk": self.project1.pk})
        )
        assert response.status_code == 200
        assert response.json()["id"] == self.project1.pk

    def test_list_projects_filtered(self):
        response = self.client.get(
            reverse("api2-projects-list"), {"title": self.project1.title}
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == self.project1.pk

    def test_retrieve_project_not_found(self):
        response = self.client.get(reverse("api2-projects-detail", kwargs={"pk": 9999}))
        assert response.status_code == 404
