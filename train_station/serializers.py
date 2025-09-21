from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from train_station.models import (
    TrainType,
    Station,
    Crew,
    Journey,
    Order,
    Route,
    Train,
    Ticket
)


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = (
            "id",
            "name",
            "latitude",
            "longitude"
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name"
        )


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type"
        )


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "image"
        )


class TrainDetailSerializer(TrainSerializer):
    train_type = TrainTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "image"
        )


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "distance", "source", "destination")


class RouteListSerializer(RouteSerializer):
    source_name = serializers.CharField(
        source="station.name",
        read_only=True
    )
    destination_name = serializers.CharField(
        source="station.name",
        read_only=True
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "distance",
            "source_name",
            "destination_name"
        )


class RouteDetailSerializer(RouteSerializer):
    source = StationSerializer(many=False, read_only=True)
    destination = StationSerializer(many=False, read_only=True)


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time"
        )


class JourneyListSerializer(JourneySerializer):
    source_name = serializers.CharField(
        source="station.name",
        read_only=True
    )
    destination_name = serializers.CharField(
        source="station.name",
        read_only=True
    )
    train_name = serializers.CharField(
        source="train.name",
        read_only=True
    )
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "source_name",
            "destination_name",
            "train_name",
            "crew",
            "departure_time",
            "arrival_time",
            "tickets_available"
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"].train,
            ValidationError
        )

        return data

    class Meta:
        model = Ticket
        fields = (
            "id",
            "cargo",
            "seat",
            "journey"
        )


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = (
            "cargo",
            "seat"
        )


class JourneyDetailSerializer(JourneySerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainListSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "taken_places"
        )
