from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import Station
from train_station.serializers import StationSerializer

STATION_URL = reverse("train_station:station-list")


class UnauthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(STATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.station1 = Station.objects.create(name="Test_name1", latitude=13.23, longitude=12.21)
        self.station2 = Station.objects.create(name="Test_name2", latitude=11.23, longitude=15.21)

    def test_list_stations(self):
        res = self.client.get(STATION_URL)

        stations = Station.objects.order_by("id")
        serializer = StationSerializer(stations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_station_forbidden(self):
        payload = {
            "name": "Sample_name",
            "latitude": 12.42,
            "longitude": 32.23
        }
        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_station(self):
        payload = {
            "name": "Sample_name",
            "latitude": 12.42,
            "longitude": 32.23
        }
        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
