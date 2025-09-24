from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import TrainType, Station, Route, Journey, Crew, Train
from train_station.serializers import TrainListSerializer, TrainDetailSerializer, RouteListSerializer, \
    RouteDetailSerializer

ROUTE_URL = reverse("train_station:route-list")


def sample_route(**params):
    defaults = {
        "source": None,
        "destination": None,
        "distance": 503,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def detail_url(route_id):
    return reverse("train_station:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.station1 = Station.objects.create(name="Test_name1", latitude=13.23, longitude=12.21)
        self.station2 = Station.objects.create(name="Test_name2", latitude=11.23, longitude=15.21)
        self.route1 = sample_route(source=self.station1, destination=self.station2)
        self.route2 = sample_route(source=self.station2, destination=self.station1)

    def test_list_routes(self):
        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("id")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_routes_by_source(self):
        res = self.client.get(
            ROUTE_URL, {"source": self.station1.id}
        )

        serializer1 = RouteListSerializer(self.route1)
        serializer2 = RouteListSerializer(self.route2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_routes_by_destination(self):
        res = self.client.get(
            ROUTE_URL, {"destination": self.station2.id}
        )

        serializer1 = RouteListSerializer(self.route1)
        serializer2 = RouteListSerializer(self.route2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_route_detail(self):
        url = detail_url(self.route1.id)
        res = self.client.get(url)

        serializer = RouteDetailSerializer(self.route1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        payload = {
            "source": self.station1.id,
            "destination": self.station2.id,
            "distance": 120,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.station1 = Station.objects.create(name="Test_name1", latitude=13.23, longitude=12.21)
        self.station2 = Station.objects.create(name="Test_name2", latitude=11.23, longitude=15.21)

    def test_create_route(self):
        payload = {
            "source": self.station1.id,
            "destination": self.station2.id,
            "distance": 120,
        }
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
