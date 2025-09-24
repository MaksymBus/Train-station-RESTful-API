from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from django.test import TestCase
from django.urls import reverse

from user.serializers import UserSerializer


class UserApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_and_manage_user(self) -> None:
        payload = {
            "email": "test@user.com",
            "password": "test123user"
        }
        response = self.client.post(reverse("user:create"), payload)
        user = get_user_model().objects.get(email=response.data["email"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["email"], user.email)
        self.assertTrue(user.check_password(payload["password"]))

        self.client.force_authenticate(user)
        response = self.client.get(reverse("user:manage"))
        serializer = UserSerializer(user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

        updated_data = {
            "email": "updated@user.com",
            "password": "updated123user"
        }

        response = self.client.patch(reverse("user:manage"), updated_data)
        user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.email, updated_data["email"])
        self.assertTrue(user.check_password(updated_data["password"]))
