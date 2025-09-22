import os
import uuid
from typing import Type

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class TrainType(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self):
        return self.name


def train_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/trains/", filename)


class Train(models.Model):
    name = models.CharField(
        max_length=255
    )
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        related_name="trains",
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        null=True,
        upload_to=train_image_file_path
    )

    class Meta:
        ordering = ["name",]

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.first_name + " " + self.last_name


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ["name",]

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        related_name="departing_routes",
        on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Station,
        related_name="arriving_routes",
        on_delete=models.CASCADE
    )
    distance = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_source_destination"
            )
        ]

    def clean(self):
        if self.source == self.destination:
            raise ValidationError("Source and destination can't be the same")

    def save(
        self,
        *args,
        **kwargs
    ):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.source} - {self.destination}"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        related_name="journeys",
        on_delete=models.CASCADE
    )
    train = models.ForeignKey(
        Train,
        related_name="journeys",
        on_delete=models.CASCADE
    )
    crew = models.ManyToManyField(Crew, blank=True, related_name="journeys")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    def clean(self):
        if self.departure_time >= self.arrival_time:
            raise ValidationError(
                "Departure time can't be more or equal to arrival time"
            )

    def save(
        self,
        *args,
        **kwargs
    ):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (f"Route: {self.route.source} - {self.route.destination}, "
                f"Train: {self.train.name}")


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(),
        related_name="orders",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        related_name="tickets",
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order,
        related_name="tickets",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("journey", "cargo", "seat")
        ordering = ["cargo", "seat"]

    @staticmethod
    def validate_ticket(
            cargo: int,
            seat: int,
            train: Train,
            error_to_raise: Type[ValidationError]
    ) -> None:
        if not (1 <= cargo <= train.cargo_num):
            raise error_to_raise(
                {
                    "cargo": f"Cargo number must be in available range: "
                             f"(1, {train.cargo_num})"
                }
            )
        if not (1 <= seat <= train.places_in_cargo):
            raise error_to_raise(
                {
                    "seat": f"Seat number must be in available range: "
                            f"(1, {train.places_in_cargo})"
                }
            )

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.seat,
            self.journey.train,
            ValidationError,
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{str(self.journey)} (cargo: {self.cargo}, seat: {self.seat})"
