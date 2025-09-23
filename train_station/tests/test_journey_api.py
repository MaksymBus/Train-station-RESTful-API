from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import TrainType, Station, Route, Journey, Crew, Train
from train_station.serializers import TrainListSerializer, TrainDetailSerializer, JourneyListSerializer, \
    JourneyDetailSerializer

JOURNEY_URL = reverse("train_station:journey-list")


def sample_train(**params):
    defaults = {
        "name": "Sample_train",
        "cargo_num": 10,
        "places_in_cargo": 50,
    }
    defaults.update(params)

    return Train.objects.create(**defaults)


def sample_journey(**params):
    defaults = {
        "departure_time": datetime(2025, 10, 23, 8, 0),
        "arrival_time": datetime(2025, 10, 23, 14, 0),
        "train": None,
        "route": None,
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


def detail_url(journey_id):
    return reverse("train_station:journey-detail", args=[journey_id])


class UnauthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(JOURNEY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.crew = Crew.objects.create(
            first_name="Test_name", last_name="Test_last_name"
        )
        self.station_1 = Station.objects.create(
            name="Station_1", latitude=1.23, longitude=2.22
        )
        self.station_2 = Station.objects.create(
            name="Station_2", latitude=2.23, longitude=3.22
        )
        self.route = Route.objects.create(
            source=self.station_1, destination=self.station_2, distance=233
        )
        self.train_type1 = TrainType.objects.create(name="Test_train_type1")
        self.train_type2 = TrainType.objects.create(name="Test_train_type2")
        self.train1 = sample_train(name="Sample_train1", train_type=self.train_type1)
        self.journey1 = sample_journey(train=self.train1, route=self.route)
        self.journey1.crew.add(self.crew)
        self.train2 = sample_train(name="Sample_train2", train_type=self.train_type2)
        self.journey2 = sample_journey(train=self.train2, route=self.route)
        self.journey2.crew.add(self.crew)

    def test_list_journeys(self):
        res = self.client.get(JOURNEY_URL)

        journeys = (
            Journey.objects.select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
            .order_by("id")
        )
        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_journeys_by_train(self):
        res = self.client.get(
            JOURNEY_URL, {"train": self.train1.id}
        )

        expected_journeys = (
            Journey.objects.filter(id=self.journey1.id)
            .select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        )

        serializer = JourneyListSerializer(expected_journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data[0], res.data["results"])

    def test_filter_journeys_by_route(self):
        res = self.client.get(
            JOURNEY_URL, {"route": self.route.id}
        )

        expected_journeys = (
            Journey.objects.filter(id=self.journey1.id)
            .select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        )

        serializer = JourneyListSerializer(expected_journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data[0], res.data["results"])

    def test_filter_journeys_by_crew(self):
        res = self.client.get(
            JOURNEY_URL, {"crew": self.crew.id}
        )

        expected_journeys = (
            Journey.objects.filter(id=self.journey1.id)
            .select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        )

        serializer = JourneyListSerializer(expected_journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data[0], res.data["results"])

    def test_filter_journeys_by_departure_time(self):
        res = self.client.get(
            JOURNEY_URL, {"departure_time": self.journey1.departure_time.date()}
        )

        expected_journeys = (
            Journey.objects.filter(id=self.journey1.id)
            .select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        )

        serializer = JourneyListSerializer(expected_journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data[0], res.data["results"])

    def test_filter_journeys_by_arrival_time(self):
        res = self.client.get(
            JOURNEY_URL, {"arrival_time": self.journey1.arrival_time.date()}
        )

        expected_journeys = (
            Journey.objects.filter(id=self.journey1.id)
            .select_related("route", "train")
            .prefetch_related("crew")
            .annotate(
                tickets_available=(
                        F("train__cargo_num") * F("train__places_in_cargo")
                        - Count("tickets")
                )
            )
        )

        serializer = JourneyListSerializer(expected_journeys, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data[0], res.data["results"])

    def test_retrieve_journey_detail(self):
        url = detail_url(self.journey1.id)
        res = self.client.get(url)

        serializer = JourneyDetailSerializer(self.journey1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_journey_forbidden(self):
        payload = {
            "departure_time": datetime(2025, 10, 23, 8, 0),
            "arrival_time": datetime(2025, 10, 23, 14, 0),
            "train": self.train1.id,
            "route": self.route.id,
        }
        res = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminJourneyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.crew = Crew.objects.create(
            first_name="Test_name", last_name="Test_last_name"
        )
        self.station_1 = Station.objects.create(
            name="Station_1", latitude=1.23, longitude=2.22
        )
        self.station_2 = Station.objects.create(
            name="Station_2", latitude=2.23, longitude=3.22
        )
        self.route = Route.objects.create(
            source=self.station_1, destination=self.station_2, distance=233
        )
        self.train_type1 = TrainType.objects.create(name="Test_train_type1")
        self.train_type2 = TrainType.objects.create(name="Test_train_type2")
        self.train1 = sample_train(name="Sample_train1", train_type=self.train_type1)
        self.journey1 = sample_journey(train=self.train1, route=self.route)
        self.journey1.crew.add(self.crew)
        self.train2 = sample_train(name="Sample_train2", train_type=self.train_type2)
        self.journey2 = sample_journey(train=self.train2, route=self.route)
        self.journey2.crew.add(self.crew)

    def test_create_journey(self):
        payload = {
            "departure_time": datetime(2025, 10, 23, 8, 0),
            "arrival_time": datetime(2025, 10, 23, 14, 0),
            "train": self.train1.id,
            "route": self.route.id,
        }
        res = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_journey(self):
        payload = {
            "departure_time": datetime(2025, 10, 23, 8, 0),
            "arrival_time": datetime(2025, 10, 23, 14, 0),
            "train": self.train2.id,
            "route": self.route.id,
        }

        url = detail_url(self.journey1.id)

        res = self.client.put(url, payload)
        self.journey1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.journey1.train, self.train2)

    def test_delete_journey(self):
        url = detail_url(self.journey1.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Journey.objects.filter(id=self.journey1.id).exists())
