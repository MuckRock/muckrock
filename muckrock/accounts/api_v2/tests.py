# Django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Third Party
from rest_framework import status

# MuckRock
from muckrock.core.factories import UserFactory

class UserViewSetTests(TestCase):
    """Test suite for the User ViewSet."""

    def setUp(self):
        """Set up test cases, creating users using UserFactory."""
        self.client = Client()

        # Create users using UserFactory
        self.user1 = UserFactory(username="jdoe", email="jdoe@example.com")
        self.user2 = UserFactory(username="asmith", email="asmith@example.com")

        # Create a staff user
        self.staff_user = UserFactory(username="admin", email="admin@example.com", is_staff=True)

        # API URLs
        self.list_url = reverse("api2-users-list")
        self.detail_url = reverse("api2-users-detail", args=["me"])

    def test_list_users(self):
        """Test retrieving the list of users."""
        # Staff user should see all users
        self.client.force_login(self.staff_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify both users are returned
        response_data = response.json()
        usernames = [user["username"] for user in response_data]
        self.assertIn("jdoe", usernames)
        self.assertIn("asmith", usernames)

    def test_filter_by_username(self):
        """Test filtering users by username."""
        self.client.force_login(self.staff_user)  # Simulate staff authentication
        response = self.client.get(self.list_url, {"username": "jdoe"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify filtered result
        response_data = response.json()
        usernames = [user["username"] for user in response_data]
        self.assertIn("jdoe", usernames)
        self.assertNotIn("asmith", usernames)

    def test_access_current_user_by_me(self):
        """Test accessing the current user by using 'me'."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("api2-users-detail", args=["me"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the current user is returned
        response_data = response.json()
        self.assertEqual(response_data["username"], "jdoe")
        self.assertEqual(response_data["full_name"], self.user1.profile.full_name)

    def test_permission_checks_for_non_staff_vs_staff(self):
        """Test the difference in behavior between staff and regular users."""
        
        # Regular user should only see their own user data
        self.client.force_login(self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the regular user only sees themselves
        response_data = response.json()
        usernames = [user["username"] for user in response_data]
        self.assertIn("jdoe", usernames)
        self.assertNotIn("asmith", usernames)  # Ensure they can't see other users

        # Staff user should see all users
        self.client.force_login(self.staff_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the staff user can see both users
        response_data = response.json()
        usernames = [user["username"] for user in response_data]
        self.assertIn("jdoe", usernames)
        self.assertIn("asmith", usernames)
        self.assertIn('admin', usernames)
