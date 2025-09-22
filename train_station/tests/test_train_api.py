import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import TrainType, Station, Route, Journey, Crew, Train
from train_station.serializers import TrainListSerializer, TrainDetailSerializer

TRAIN_URL = reverse("train_station:train-list")
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
    station_1 = Station.objects.create(
        name="Station_1", latitude=1.23, longitude=2.22
    )
    station_2 = Station.objects.create(
        name="Station_2", latitude=2.23, longitude=3.22
    )
    route = Route.objects.create(
        source=station_1, destination=station_2, distance=233
    )

    defaults = {
        "departure_time": "2022-06-02 14:00:00",
        "arrival_time": "2022-06-03 12:00:00",
        "train": None,
        "route": route,
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for recipe image upload"""
    return reverse("train_station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("train_station:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        self.train_type1 = TrainType.objects.create(name="Test_train_type_1")
        self.train_type2 = TrainType.objects.create(name="Test_train_type_2")
        self.train1 = sample_train(name="Sample_train1", train_type=self.train_type1)
        self.train2 = sample_train(name="Sample_train2", train_type=self.train_type2)

    def test_list_trains(self):
        res = self.client.get(TRAIN_URL)

        trains = Train.objects.order_by("id")
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_trains_by_train_type(self):
        res = self.client.get(
            TRAIN_URL, {"train_type": self.train_type1.id}
        )

        serializer1 = TrainListSerializer(self.train1)
        serializer2 = TrainListSerializer(self.train2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_trains_by_name(self):
        res = self.client.get(
            TRAIN_URL, {"name": self.train1.name}
        )

        serializer1 = TrainListSerializer(self.train1)
        serializer2 = TrainListSerializer(self.train2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotEqual(serializer2.data, res.data["results"])

    def test_retrieve_train_detail(self):
        url = detail_url(self.train1.id)
        res = self.client.get(url)

        serializer = TrainDetailSerializer(self.train1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "Sample_train",
            "cargo_num": 10,
            "places_in_cargo": 50,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.train_type1 = TrainType.objects.create(name="Test_train_type_1")
        self.train_type2 = TrainType.objects.create(name="Test_train_type_2")

    def test_create_train(self):
        payload = {
            "name": "Sample_train",
            "cargo_num": 10,
            "places_in_cargo": 50,
            "train_type": self.train_type1.id
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class MovieImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.crew = Crew.objects.create(
            first_name="Test_name", last_name="Test_last_name"
        )
        self.train_type = TrainType.objects.create(name="Test_train_type")
        self.train = sample_train(name="Sample_train", train_type=self.train_type)
        self.journey = sample_journey(train=self.train)
        self.journey.crew.add(self.crew)


    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list_should_not_work(self):
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Test_train",
                    "cargo_num": 10,
                    "places_in_cargo": 50,
                    "train_type": self.train_type.id,
                    "image": ntf
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Test_train")
        self.assertFalse(train.image)

    def test_image_url_is_shown_on_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.train.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data["results"][0].keys())

    def test_put_train_not_allowed(self):
        payload = {
            "name": "New_train",
            "cargo_num": 10,
            "places_in_cargo": 50,
            "train_type": self.train_type.id,
        }

        url = detail_url(self.train.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_train_not_allowed(self):
        url = detail_url(self.train.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
