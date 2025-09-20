from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from train_station.models import TrainType, Station


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


