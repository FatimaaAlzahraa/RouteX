from rest_framework import serializers
from django.utils import timezone
from users.models import CustomUser
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import (
    WarehouseManager, Warehouse, Customer, Shipment,
    StatusUpdate, Driver,Product
)


class ProductSerializer(serializers.ModelSerializer):
    shipments_count = serializers.IntegerField(read_only=True)
    class Meta:
        model  = Product
        fields = ["id", "name", "price", "unit", "stock_qty", "is_active",
                  "created_at", "shipments_count"]
        read_only_fields = ["created_at", "shipments_count"]

class ShipmentSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), required=False, allow_null=True
    )
    driver_username = serializers.CharField(source="driver.user.username", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "warehouse",
            "product",      
            "product_name", 
            "driver",
            "driver_username",
            "customer",
            "customer_name",
            "customer_address",
            "notes",
            "current_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at", "updated_at", "current_status",
            "driver_username", "customer_name", "product_name",
        ]

    def _customer_addresses_list(self, customer: Customer):
        return [
            v for v in [
                getattr(customer, "address", None),
                getattr(customer, "address2", None),
                getattr(customer, "address3", None),
            ] if v
        ]

    def validate(self, attrs):
        request = self.context["request"]

        # الإنشاء/التعديل: مدير المخزن فقط
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("Only warehouse managers can create/update shipments.")

        customer = attrs.get("customer", getattr(self.instance, "customer", None))

        if not customer:
            attrs["customer_address"] = None
            return attrs

        allowed = self._customer_addresses_list(customer)
        if not allowed:
            raise ValidationError({"customer_address": "Customer has no saved addresses to use."})

        addr = attrs.get("customer_address", None)
        addr_clean = None if addr is None else str(addr).strip()

        if not addr_clean:
            raise ValidationError({
                "customer_address": "Customer selected. You must choose one of the customer's saved addresses.",
                "allowed_addresses": allowed,
            })

        if addr_clean not in allowed:
            raise ValidationError({
                "customer_address": "Address must be one of the customer's saved addresses.",
                "allowed_addresses": allowed,
            })

        attrs["customer_address"] = addr_clean
        return attrs



# WAREHOUSE
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("Only warehouse managers can create/update warehouses.")
        return attrs

# CUSTOMERS
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "address2" , "address3" ,"created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("Only warehouse managers can create/update customers.")
        

        addr  = (attrs.get("address") or "").strip()
        addr2 = (attrs.get("address2") or "").strip()
        addr3 = (attrs.get("address3") or "").strip()
        if not (addr or addr2 or addr3):
            raise ValidationError({"address": "Provide at least one of: address / address2 / address3."})
        return attrs
    def to_representation(self, instance):
        # drop empty addresses from output
        data = super().to_representation(instance)
        for key in ["address", "address2", "address3"]:
            if not data.get(key): 
                data.pop(key, None)
        return data

# STATUSUPDATE
class StatusUpdateSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(read_only=True)
    customer_name = serializers.CharField(source="shipment.customer.name", read_only=True)
    customer_phone = serializers.CharField(source="shipment.customer.phone", read_only=True)

    class Meta:
        model = StatusUpdate
        fields = ["id", "shipment", "customer_name", "customer_phone", "status", "timestamp", "note",
                  "photo", "latitude", "longitude", "location_accuracy_m"]  

    def validate(self, attrs):
        request = self.context["request"]

        # must be a driver with profile
        try:
            driver_profile = Driver.objects.get(user=request.user)
        except Driver.DoesNotExist:
            raise PermissionDenied("Only drivers can create status updates.")

        shipment: Shipment = attrs["shipment"]
        if not shipment.driver or shipment.driver_id != driver_profile.id:
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




# DRIVER STATUS

class DriverStatusSerializer(serializers.ModelSerializer):
    name   = serializers.CharField(source="user.username", read_only=True)
    phone  = serializers.CharField(source="user.phone", read_only=True)
    status = serializers.SerializerMethodField()
    # اختياري: لو عايز ترجعهم للـ UI
    last_seen_at = serializers.DateTimeField(read_only=True)
    current_active_shipment_id = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Driver
        fields = [
            "id",
            "name",
            "phone",
            "status",
            "last_seen_at",
            "current_active_shipment_id",
        ]

    def get_status(self, obj):
        # busy if has active shipment
        if getattr(obj, "current_active_shipment_id", None):
            return "مشغول"
        # available if effectively active
        if getattr(obj, "effective_is_active", False):
            return "متاح"
        return "غير متاح"
