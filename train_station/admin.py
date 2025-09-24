from django.contrib import admin

from train_station.models import (
    Journey,
    Train,
    TrainType,
    Crew,
    Ticket,
    Station,
    Route,
    Order
)


admin.site.register(Journey)
admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Crew)
admin.site.register(Ticket)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Order)
