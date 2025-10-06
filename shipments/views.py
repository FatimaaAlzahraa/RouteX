# shipments/views.py
from rest_framework import generics 
from django.db.models import Exists, OuterRef, Subquery, Case, When, Value, BooleanField, F
from django.db.models import Exists, OuterRef, Subquery
from rest_framework import viewsets, filters
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.dateparse import parse_datetime
from rest_framework import serializers as drf_serializers
from .permissions import IsWarehouseManager, IsDriver
from .models import Shipment, StatusUpdate, WarehouseManager, Customer, Warehouse, Driver
from .serializers import (
    StatusUpdateSerializer,ShipmentSerializer,
    CustomerSerializer, WarehouseSerializer, DriverStatusSerializer
)


# 1) Shipment create (warehouse manager only)
class ShipmentCreateView(generics.CreateAPIView):
    queryset = Shipment.objects.select_related("warehouse", "driver__user", "customer")
    serializer_class = ShipmentSerializer
    permission_classes = [IsWarehouseManager]

# 2) detail/update/delete shipment (warehouse manager only)
class ShipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shipment.objects.select_related("warehouse", "driver__user", "customer")
    serializer_class = ShipmentSerializer
    permission_classes = [IsWarehouseManager]

    def get_queryset(self):
        return (self.queryset if WarehouseManager.objects.filter(user=self.request.user).exists()
                else Shipment.objects.none())


# 3) system-wide shipments list (warehouse manager only)
class ShipmentsListView(generics.ListAPIView):
    permission_classes = [IsWarehouseManager]
    serializer_class = ShipmentSerializer  

    def get_queryset(self):
        if not WarehouseManager.objects.filter(user=self.request.user).exists():
            return Shipment.objects.none()

        qs = Shipment.objects.select_related("warehouse", "driver__user", "customer")
        updated_since = self.request.query_params.get("updated_since")
        if updated_since:
            dt = parse_datetime(updated_since)
            if dt:
                qs = qs.filter(updated_at__gte=dt)
        return qs.order_by("-updated_at")[:500]


# 4) Autocomplete shipments (warehouse manager only)
class AutocompleteShipmentsView(generics.ListAPIView):
    serializer_class = ShipmentSerializer  
    permission_classes = [IsWarehouseManager]

    def get_queryset(self):
        if not WarehouseManager.objects.filter(user=self.request.user).exists():
            return Shipment.objects.none()

        q = (self.request.query_params.get("q") or "").strip()
        qs = Shipment.objects.select_related("customer", "driver__user", "warehouse")
        if q:
            if q.isdigit():
                qs = qs.filter(id=int(q))
            else:
            # search in shipment_details text field
                qs = qs.filter(shipment_details__icontains=q)
        return qs.order_by("-updated_at")[:20]




# 5) warehouse create (warehouse manager only)
class WarehouseCreateView(generics.CreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsWarehouseManager]

# 6) detail/update/delete customer (warehouse manager only)
class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsWarehouseManager]


# 6) detail/update/delete warehouse (warehouse manager only)
class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [IsWarehouseManager]
    queryset = Warehouse.objects.all()

    def get_queryset(self):
        try:
            WarehouseManager.objects.get(user=self.request.user)
        except WarehouseManager.DoesNotExist:
            return Warehouse.objects.none()
        return self.queryset




# 7) customer create (warehouse manager only)
class CustomerCreateView(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsWarehouseManager]


# 8) Autocomplete customers (warehouse manager only)
class AutocompleteCustomersView(generics.ListAPIView):
    """
    search param: q
      - q isdigit => match id/phone
      - q text => match name/phone
    20 results max, ordered by -updated_at
    without WM profile => empty queryset
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsWarehouseManager]

    def get_queryset(self):
        q = (self.request.query_params.get("q") or "").strip()

        # لازم WM profile
        if not WarehouseManager.objects.filter(user=self.request.user).exists():
            return Customer.objects.none()

        qs = Customer.objects.all()

        if q:
            if q.isdigit():
                qs = qs.filter(Q(id=int(q)) | Q(phone__icontains=q))
            else:
                qs = qs.filter(
                    Q(name__icontains=q) |
                    Q(phone__icontains=q) 
                )

        return qs.order_by("-updated_at")[:20]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        # fields to keep in this endpoint
        keep = {"id", "name", "phone", "address"} 

        if isinstance(serializer, drf_serializers.ListSerializer):
            fields = serializer.child.fields
        else:
            fields = serializer.fields

        for name in list(fields):
            if name not in keep:
                fields.pop(name)

        return serializer





# 9) list shipments assigned to the logged-in driver
class DriverShipmentsList(generics.ListAPIView):
    serializer_class = ShipmentSerializer
    permission_classes = [IsDriver]

    def get_queryset(self):
        return (Shipment.objects
                .select_related("driver__user", "warehouse", "customer")
                .filter(driver__user=self.request.user)
                .order_by("-assigned_at"))

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)

        # fields to keep in this endpoint
        keep = {
            "id",
            "warehouse",
            "shipment_details",
            "driver", "driver_username",
            "customer_display_name",
            "customer_address",
            "notes",
            "current_status",
            "created_at", "updated_at",
        }

        if isinstance(serializer, drf_serializers.ListSerializer):
            fields = serializer.child.fields  
        else:
            fields = serializer.fields

        # cancelled field is excluded
        for name in list(fields):
            if name not in keep:
                fields.pop(name)

        return serializer
    

# 10) driver posts a status update for a shipment
class StatusUpdateCreateView(generics.CreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    queryset = StatusUpdate.objects.select_related("shipment", "shipment__driver")
    serializer_class = StatusUpdateSerializer
    permission_classes = [IsDriver]




class DriverStatusView(viewsets.ReadOnlyModelViewSet):
    serializer_class = DriverStatusSerializer
    permission_classes = [IsWarehouseManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "user__phone"]

    def get_queryset(self):
        latest_update_qs = (
            StatusUpdate.objects
            .filter(shipment__driver=OuterRef("pk"))
            .order_by("-timestamp")
        )

        ACTIVE_STATUSES = ["ASSIGNED", "IN_TRANSIT"]
        active_shipment_qs = (
            Shipment.objects
            .filter(driver=OuterRef("pk"))
            .annotate(
                _last_status=Subquery(
                    StatusUpdate.objects
                    .filter(shipment=OuterRef("pk"))
                    .order_by("-timestamp")
                    .values("status")[:1]
                )
            )
            .filter(_last_status__in=ACTIVE_STATUSES)
            .order_by("-updated_at")
            .values("id")[:1]
        )

        qs = (
            Driver.objects.select_related("user")
            .annotate(
                last_status   = Subquery(latest_update_qs.values("status")[:1]),
                last_seen_at  = Subquery(latest_update_qs.values("timestamp")[:1]),
                current_active_shipment_id = Subquery(active_shipment_qs),
            )
            .annotate(
                effective_is_active=Case(
                    When(last_status="DELIVERED", then=Value(True)),
                    default=F("is_active"),
                    output_field=BooleanField(),
                )
            )
            .order_by("user__username", "pk")
        )
        return qs