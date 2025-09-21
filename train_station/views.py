from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from train_station.models import (
    TrainType,
    Crew,
    Journey,
    Train,
    Route,
    Station,
    Ticket,
    Order
)
from train_station.serializers import (
    TrainTypeSerializer,
    CrewSerializer,
    StationSerializer, TrainSerializer, TrainListSerializer, TrainDetailSerializer, TrainImageSerializer,
    RouteListSerializer, RouteDetailSerializer, RouteSerializer,
)


class TrainTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class StationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class TrainViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Train.objects.select_related("train_type")

    def get_queryset(self):
        name = self.request.query_params.get("name")
        train_type_id_str = self.request.query_params.get("train_type")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        if train_type_id_str:
            queryset = queryset.filter(train_type_id=int(train_type_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer

        if self.action == "retrieve":
            return  TrainDetailSerializer

        if self.action == "upload_image":
            return  TrainImageSerializer

        return TrainSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "train_type",
                type=OpenApiTypes.INT,
                description="Filter by train_type id (ex. ?train_type=2)",
            ),
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description=(
                        "Filter by name of Train "
                        "(ex. ?name=Intercity)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
