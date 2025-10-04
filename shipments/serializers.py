from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from users.models import CustomUser
from .models import (
    WarehouseManager, Warehouse, Customer, Shipment,
    StatusUpdate, Driver
)


# SHIPMENTS 
class ShipmentSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(write_only=True, required=False)
    driver_display_name = serializers.CharField(source="driver.user.name", read_only=True)
    customer_display_name = serializers.CharField(source="customer.name", read_only=True)
    customer_address = serializers.CharField(source="customer.address", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "warehouse",
            "driver",
            "driver_name",            
            "driver_display_name",   
            "customer",
            "customer_display_name",  
            "customer_address",
            "shipment_details",
            "notes",
            "current_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at", "updated_at", "current_status",
            "driver_display_name", "customer_display_name","customer_address",
        ]


    def _resolve_driver_by_name(self, name: str):
        name = (name or "").strip()
        qs = Driver.objects.select_related("user").filter(user__name__iexact=name)
        cnt = qs.count()
        if cnt == 0:
            raise ValidationError({"driver_name": "No driver found with this name."})
        if cnt > 1:
            raise ValidationError({"driver_name": "Multiple drivers share this name. Please use driver (id)."})
        return qs.first()

    def validate(self, attrs):
        request = self.context["request"]

        # only warehouse managers can create/update shipments
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create/update shipments.")
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("No warehouse manager profile for this user.")
        

        # driver_name logic + validation
        driver_pk_or_instance = attrs.get("driver")
        driver_name = (self.initial_data or {}).get("driver_name")

        if not driver_pk_or_instance and driver_name:
            attrs["driver"] = self._resolve_driver_by_name(driver_name)

        if driver_pk_or_instance and driver_name:
            resolved = self._resolve_driver_by_name(driver_name)
            given_id = getattr(driver_pk_or_instance, "id", driver_pk_or_instance)
            if int(given_id) != resolved.id:
                raise ValidationError({"driver": "driver id conflicts with driver_name. Use one or make them match."})

        return attrs




# WAREHOUSE
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER: 
            raise PermissionDenied("Only warehouse managers can create/update warehouses.")
        return attrs
    




# CUSTOMERS
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create/update customers.")
        return attrs




# STATUSUPDATE
class StatusUpdateSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StatusUpdate
        fields = ["id", "shipment", "status", "timestamp", "note",
                  "photo", "latitude", "longitude", "location_accuracy_m"]  

    def validate(self, attrs):
        request = self.context["request"]
        if getattr(request.user, "role", None) != CustomUser.Roles.DRIVER:
            raise PermissionDenied("Only drivers can create status updates.")

        shipment: Shipment = attrs["shipment"]
        if not shipment.driver or shipment.driver.user_id != request.user.id:
            raise PermissionDenied("You can only update the status of your own shipment.")

        # GPS accuracy ≤ 30 meters validation
        acc = attrs.get("location_accuracy_m")
        if acc is not None and acc > 30:
            raise serializers.ValidationError({"location_accuracy_m": "GPS accuracy must be ≤ 30 meters."})
        
        # both latitude and longitude must be provided together
        lat, lng = attrs.get("latitude"), attrs.get("longitude")
        if (lat is None) ^ (lng is None):
            raise serializers.ValidationError("Both latitude and longitude are required together.")
        return attrs

    def create(self, validated_data):
        validated_data["timestamp"] = timezone.now()
        return super().create(validated_data)



