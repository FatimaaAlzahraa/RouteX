from rest_framework import serializers
from django.utils import timezone
from users.models import CustomUser
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import (
    WarehouseManager, Warehouse, Customer, Shipment,
    StatusUpdate, Driver, Product
)


# PRODUCTS
class ProductSerializer(serializers.ModelSerializer):
    shipments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "price", "unit", "stock_qty", "is_active",
            "created_at", "shipments_count"
        ]
        read_only_fields = ["created_at", "shipments_count"]



# SHIPMENTS
class ShipmentSerializer(serializers.ModelSerializer):
    # السائق يمكن أن يكون فارغ (الشحنة غير مخصصة بعد)
    driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), required=False, allow_null=True
    )
    driver_username = serializers.CharField(source="driver.user.username", read_only=True)
    customer_name   = serializers.CharField(source="customer.name", read_only=True)
    customer_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # لا يمكن وضع المنتج فارغ
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "warehouse",
            "product", "product_name",
            "driver", "driver_username",
            "customer", "customer_name",
            "customer_address",
            "notes",
            "current_status",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "created_at", "updated_at", "current_status",
            "driver_username", "customer_name", "product_name",
        ]

    def _customer_addresses_list(self, customer: Customer):
        # إرجاع جميع حقول العناوين غير الفارغة للعميل
        return [v for v in [
            getattr(customer, "address", None),
            getattr(customer, "address2", None),
            getattr(customer, "address3", None),
        ] if v]


    def _reserve_stock(self, product: Product, qty: int = 1):
        #انخفض المخزون تدريجيًا إذا توفرت كمية كافية
        updated = Product.objects.filter(
            pk=product.pk, stock_qty__gte=qty
        ).update(stock_qty=F("stock_qty") - qty)
        if updated == 0:
            raise ValidationError({"المنتج": "عدد المخزن غير كافي."})

    def _release_stock(self, product: Product, qty: int = 1):
        # زيادة المخزون مرة أخرى (يستخدم عند تغيير المنتج)
        Product.objects.filter(pk=product.pk).update(stock_qty=F("stock_qty") + qty)

    # validation 
    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("يمكن فقط لمديري المستودعات إنشاء/تحديث الشحنات.")

        #  العميل وعنوانه
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        if not customer:
            attrs["customer_address"] = None
        else:
            allowed = self._customer_addresses_list(customer)
            if not allowed:
                raise ValidationError({"customer_address": "ليس لدى العميل أي عناوين محفوظة لاستخدامها."})

            addr = attrs.get("customer_address", getattr(self.instance, "customer_address", None))
            addr_clean = None if addr is None else str(addr).strip()

            if not addr_clean:
                # Customer chosen but no address provided
                raise ValidationError({
                    "customer_address": "تم اختيار العميل. يجب عليك اختيار أحد عناوين العميل المحفوظة.",
                    "allowed_addresses": allowed,
                })

            if addr_clean not in allowed:
                # Address must be one of the customer's addresses
                raise ValidationError({
                    "customer_address": "يجب أن يكون العنوان أحد العناوين المحفوظة لدى العميل.",
                    "allowed_addresses": allowed,
                })

            attrs["customer_address"] = addr_clean

        new_driver  = attrs.get("driver",  getattr(self.instance, "driver",  None))
        new_product = attrs.get("product", getattr(self.instance, "product", None))

        #  التأكد من المخزون عندما يتم تعيين سائق بمنتج
        need_new_reservation = False
        if new_driver and new_product:
            if self.instance is None:
                need_new_reservation = True
            else:
                old_driver  = self.instance.driver
                old_product = self.instance.product
                if not old_driver:
                    # Previously no driver, now driver assigned
                    need_new_reservation = True
                elif old_product != new_product:
                    # Product changed while driver remains assigned
                    need_new_reservation = True

        if need_new_reservation and new_product and new_product.stock_qty <= 0:
            # Fast-fail before hitting DB update
            raise ValidationError({"المنتج": "الكمية المتوفرة في المخزون غير كافية"})

        return attrs

    # ------- create/update -------
    @transaction.atomic
    def create(self, validated_data):
        # إنشاء شحنة، ثم حجز المخزون إذا تم تعيين كل من السائق والمنتج
        driver  = validated_data.get("driver")
        product = validated_data.get("product")

        obj = super().create(validated_data)

        if driver and product:
            self._reserve_stock(product, 1)

        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # تحديث الشحنة ومطابقة المخزون عند تغيير التعيين (السائق، المنتج).
        old_driver  = instance.driver
        old_product = instance.product

        new_driver  = validated_data.get("driver",  old_driver)
        new_product = validated_data.get("product", old_product)

        obj = super().update(instance, validated_data)

        # Cases:
        if not old_driver and new_driver:
            # Driver assigned now
            if new_product:
                self._reserve_stock(new_product, 1)

        elif old_driver and not new_driver:
            # Driver removed
            if old_product:
                self._release_stock(old_product, 1)

        elif old_driver and new_driver and old_product != new_product:
            # Same driver but product replaced
            if old_product:
                self._release_stock(old_product, 1)
            if new_product:
                self._reserve_stock(new_product, 1)

        return obj



# WAREHOUSE (المستودعات)
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("يمكن لمديري المستودعات فقط إنشاء/تحديث المستودعات")

        # Normalize inputs 
        name     = (attrs.get("name",     getattr(self.instance, "name",     "")) or "").strip()
        location = (attrs.get("location", getattr(self.instance, "location", "")) or "").strip()

        if not name:
            raise ValidationError({"الاسم": "اسم المستودع مطلوب"})
        if not location:
            raise ValidationError({"الموقع": "الموقع/العنوان مطلوب"})

        attrs["name"] = name
        attrs["location"] = location

        #يمنع تكرار نفس الاسم والموقع معا 
        qs = Warehouse.objects.filter(name__iexact=name, location__iexact=location)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError({
                "non_field_errors": ["يوجد بالفعل مستودع بنفس الاسم والعنوان."]
            })

        return attrs



# CUSTOMERS (العملاء)
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Customer
        fields = ["id", "name", "phone", "address", "address2", "address3", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("يمكن لمديري المستودعات فقط إنشاء/تحديث العملاء")

        addr  = (attrs.get("address")  or "").strip()
        addr2 = (attrs.get("address2") or "").strip()
        addr3 = (attrs.get("address3") or "").strip()

        if not (addr or addr2 or addr3):
            raise ValidationError({"العناوين": "قم بتوفير واحد على الأقل من العناوين"})

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ["address", "address2", "address3"]:
            if not data.get(key):
                data.pop(key, None)
        return data



# STATUS UPDATE (Driver) (تحديث الشحنة المعينة للسائق)
class StatusUpdateSerializer(serializers.ModelSerializer):
    # Set by server at creation time
    timestamp = serializers.DateTimeField(read_only=True)
    customer_name  = serializers.CharField(source="shipment.customer.name",  read_only=True)
    customer_phone = serializers.CharField(source="shipment.customer.phone", read_only=True)

    class Meta:
        model  = StatusUpdate
        fields = [
            "id",
            "shipment",
            "customer_name", "customer_phone",
            "status",
            "timestamp",
            "note", "photo",
            "latitude", "longitude",
            "location_accuracy_m",
        ]

    def validate(self, attrs):
        request = self.context["request"]

        # must be a driver with profile
        try:
            driver_profile = Driver.objects.get(user=request.user)
        except Driver.DoesNotExist:
            raise PermissionDenied("يمكن للسائقين فقط إنشاء تحديثات الحالة")

        shipment: Shipment = attrs["shipment"]
        if not shipment.driver or shipment.driver_id != driver_profile.id:
            raise PermissionDenied("يمكنك فقط تحديث حالة شحنتك الخاصة")

        # GPS accuracy ≤ 30 meters validation
        acc = attrs.get("location_accuracy_m")
        if acc is not None and acc > 30:
            raise serializers.ValidationError({"location_accuracy_m": "GPS accuracy must be ≤ 30 meters."})

        # both latitude and longitude must be provided together
        lat, lng = attrs.get("latitude"), attrs.get("longitude")
        if (lat is None) ^ (lng is None):
            raise serializers.ValidationError("يجب أن يكون كلا من خط العرض وخط الطول معًا")
        return attrs

    def create(self, validated_data):
        """Set server timestamp and create the status update."""
        validated_data["timestamp"] = timezone.now()
        return super().create(validated_data)



# DRIVER STATUS (for manager dashboard) حالة تحديث الشحنة من السائق تعرض في تطبيق السائق 
class DriverStatusSerializer(serializers.ModelSerializer):
    name  = serializers.CharField(source="user.username", read_only=True)
    phone = serializers.CharField(source="user.phone",    read_only=True)
    status = serializers.SerializerMethodField()
    last_seen_at = serializers.DateTimeField(read_only=True)
    current_active_shipment_id = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Driver
        fields = [
            "id",
            "name", "phone",
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
