from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import TrainType
from train_station.serializers import TrainTypeSerializer


TRAIN_TYPE_URL = reverse("train_station:traintype-list")


class UnauthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.train_type1 = TrainType.objects.create(name="Test_train_type_1")
        self.train_type2 = TrainType.objects.create(name="Test_train_type_2")

    def test_list_train_types(self):
        res = self.client.get(TRAIN_TYPE_URL)

        train_types = TrainType.objects.order_by("id")
        serializer = TrainTypeSerializer(train_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_train_type_forbidden(self):
        payload = {
            "name": "Sample_train_type",
        }
        res = self.client.post(TRAIN_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train_type(self):
        payload = {
            "name": "New_train_type",
        }
        res = self.client.post(TRAIN_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
