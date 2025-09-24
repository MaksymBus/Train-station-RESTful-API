from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from train_station.models import Order
from train_station.serializers import (
    OrderListSerializer,
)

ORDER_URL = reverse("train_station:order-list")

def sample_order(user) -> Order:
    return Order.objects.create(user=user)

def detail_url(order_id: int) -> str:
    return reverse("train_station:order-detail", args=[order_id])


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@user.com", password="testpassword"
        )
        self.client.force_authenticate(self.user)

    def test_order_list(self) -> None:
        sample_order(user=self.user)
        sample_order(user=self.user)

        res = self.client.get(ORDER_URL)
        orders = Order.objects.filter(user=self.user).order_by("-created_at")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
