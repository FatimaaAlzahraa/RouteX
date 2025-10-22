from rest_framework import serializers
from django.utils import timezone
from users.models import CustomUser
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import (
    WarehouseManager, Warehouse, Customer, Shipment,
    StatusUpdate, Driver,Product
)


# PRODUCTS
class ProductSerializer(serializers.ModelSerializer):
    shipments_count = serializers.IntegerField(read_only=True)
    class Meta:
        model  = Product
        fields = ["id", "name", "price", "unit", "stock_qty", "is_active",
                  "created_at", "shipments_count"]
        read_only_fields = ["created_at", "shipments_count"]


# SHIPMENTS
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
        return [v for v in [
            getattr(customer, "address", None),
            getattr(customer, "address2", None),
            getattr(customer, "address3", None),
        ] if v]

    def _reserve_stock(self, product: Product, qty: int = 1):

        updated = Product.objects.filter(
            pk=product.pk, stock_qty__gte=qty
        ).update(stock_qty=F("stock_qty") - qty)
        if updated == 0:
            raise ValidationError({"product": "الكمية في المخزون غير كافية."})

    def _release_stock(self, product: Product, qty: int = 1):
        Product.objects.filter(pk=product.pk).update(stock_qty=F("stock_qty") + qty)

    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("Only warehouse managers can create/update shipments.")
        
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        if not customer:
            attrs["customer_address"] = None
        else:
            allowed = self._customer_addresses_list(customer)
            if not allowed:
                raise ValidationError({"customer_address": "Customer has no saved addresses to use."})
            addr = attrs.get("customer_address", getattr(self.instance, "customer_address", None))
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

        new_driver = attrs.get("driver", getattr(self.instance, "driver", None))
        new_product = attrs.get("product", getattr(self.instance, "product", None))

        need_new_reservation = False
        if new_driver and new_product:
            if self.instance is None:
                need_new_reservation = True                    
            else:
                old_driver = self.instance.driver
                old_product = self.instance.product
                if not old_driver:                               
                    need_new_reservation = True
                elif old_product != new_product:                 
                    need_new_reservation = True

        if need_new_reservation and new_product and new_product.stock_qty <= 0:
            raise ValidationError({"product": "الكمية في المخزون غير كافية."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        driver = validated_data.get("driver")
        product = validated_data.get("product")
        obj = super().create(validated_data)
        if driver and product:
            self._reserve_stock(product, 1)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        old_driver = instance.driver
        old_product = instance.product

        new_driver = validated_data.get("driver", old_driver)
        new_product = validated_data.get("product", old_product)

        obj = super().update(instance, validated_data)

        # حالات التعديل:
        if not old_driver and new_driver:
            if new_product:
                self._reserve_stock(new_product, 1)

        elif old_driver and not new_driver:
            if old_product:
                self._release_stock(old_product, 1)

        elif old_driver and new_driver and old_product != new_product:
            if old_product:
                self._release_stock(old_product, 1)
            if new_product:
                self._reserve_stock(new_product, 1)

        return obj
    
    

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

        name = (attrs.get("name", getattr(self.instance, "name", "")) or "").strip()
        location = (attrs.get("location", getattr(self.instance, "location", "")) or "").strip()

        if not name:
            raise ValidationError({"name": "اسم المستودع مطلوب."})
        if not location:
            raise ValidationError({"location": "الموقع/العنوان مطلوب."})

        attrs["name"] = name
        attrs["location"] = location

        # منع تكرار (الاسم + العنوان) معًا 
        qs = Warehouse.objects.filter(
            name__iexact=name,
            location__iexact=location,
        )
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError({
                "non_field_errors": ["يوجد مستودع بنفس الاسم ونفس العنوان بالفعل."]
            })

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
        fields = [
            "id",
            "shipment",
            "customer_name",
            "customer_phone",
            "status",
            "timestamp",
            "note",
            "photo",
            "latitude",
            "longitude",
            "location_accuracy_m",
        ]

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
