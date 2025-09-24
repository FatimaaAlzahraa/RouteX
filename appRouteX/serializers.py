# appRouteX/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    CustomUser, WarehouseManager, Warehouse, Customer, Shipment,
    Assignment, StatusUpdate, ShipmentStatus, Driver
)
from rest_framework.exceptions import PermissionDenied

# SHIPMENTS

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "name", "warehouse", "shipment_details", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]

        # لازم يكون Warehouse Manager في الإنشاء أو التعديل
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create/update shipments.")

        # بروفايل المدير
        try:
            wm = WarehouseManager.objects.get(user=request.user)
        except WarehouseManager.DoesNotExist:
            raise PermissionDenied("No warehouse manager profile for this user.")

        # هنحدد أي مخزن هنشيّك عليه:
        #  ده تعديل/إنشاء على مخزن مبعوت
        # تعديل جزئي (PATCH)  المخزن الحالي
        wh = attrs.get("warehouse") or (self.instance.warehouse if self.instance else None)

        if wh and wh.manager_id != wm.id:
            raise serializers.ValidationError({
                "warehouse": "You can only manage shipments for warehouses you manage."
            })

        return attrs
    

class CustomerLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "updated_at"]

class ShipmentLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "name", "warehouse", "updated_at"]


#ASSIGNMENTS
class AssignmentSerializer(serializers.ModelSerializer):
    current_status = serializers.CharField(read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id", "shipment", "driver", "customer", "warehouse",
            "notes", "assigned_at", "current_status"
        ]
        read_only_fields = ["assigned_at", "current_status"]

    def validate(self, attrs):
        request = self.context["request"]

        # 1) لازم Warehouse Manager (إنشاء/تعديل)
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create/update assignments.")

        # 2) همجيب بروفايل المدير
        try:
            wm = WarehouseManager.objects.get(user=request.user)
        except WarehouseManager.DoesNotExist:
            raise PermissionDenied("No warehouse manager profile for this user.")

        # 3) جهّز القيم اللي هنشيّك عليها (من attrs أو من instance في حالة PATCH)
        #علشان نطبّق قواعد الفاليديشن حتى لو  ما حطيناش كل الحقول.
        instance = getattr(self, "instance", None)
        shipment: Shipment = attrs.get("shipment")  or (instance.shipment  if instance else None)
        warehouse: Warehouse = attrs.get("warehouse") or (instance.warehouse if instance else None)
        driver: Driver = attrs.get("driver")    or (instance.driver    if instance else None)
        customer = attrs.get("customer")  or (instance.customer  if instance else None)

        # 4) تطابق الشحنة والمخزن
        if shipment and warehouse and shipment.warehouse_id != warehouse.id:
            raise serializers.ValidationError({"warehouse": "Warehouse must match shipment.warehouse."})

        # 5) لازم يكون المدير الحالي هو مدير المخزن المستخدم
        if warehouse and warehouse.manager_id != wm.id:
            raise serializers.ValidationError({"warehouse": "You can only assign from warehouses you manage."})

        # 6) تأكد أن السائق فعلاً دوره DRIVER
        if driver and getattr(driver.user, "role", None) != CustomUser.Roles.DRIVER:
            raise serializers.ValidationError({"driver": "Selected driver must have DRIVER role."})

        # 7) منع تكرار (نفس الشحنة + نفس السائق) في Assignment آخر
        if shipment and driver:
            qs = Assignment.objects.filter(shipment=shipment, driver=driver)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"driver": "This driver is already assigned to this shipment."})

        return attrs
    

class WarehouseSerializer(serializers.ModelSerializer):
    # بنخلّي المدير يتحدد تلقائيًا من اليوزر اللي عامل الطلب
    manager = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "manager", "created_at", "updated_at"]
        read_only_fields = ["manager", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create/update warehouses.")
        # لازم يكون عنده WarehouseManager profile
        if not WarehouseManager.objects.filter(user=request.user).exists():
            raise PermissionDenied("No warehouse manager profile for this user.")
        return attrs

    def create(self, validated_data):
        wm = WarehouseManager.objects.get(user=self.context["request"].user)
        validated_data["manager"] = wm
        return super().create(validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address"]

    def validate(self, attrs):
        request = self.context["request"]
        if getattr(request.user, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise PermissionDenied("Only warehouse managers can create customers.")
        return attrs
    

#STATEUPDATE
class StatusUpdateSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StatusUpdate
        fields = ["id", "assignment", "status", "timestamp", "note", "attachment_url"]

    def validate(self, attrs):
        request = self.context["request"]
        # لازم يبقى Driver
        if getattr(request.user, "role", None) != CustomUser.Roles.DRIVER:
            raise PermissionDenied("Only drivers can create status updates.")

        # لازم يكون هو نفس سائق الـ Assignment
        assignment: Assignment = attrs["assignment"]
        if assignment.driver.user_id != request.user.id:
            raise PermissionDenied("You can only update the status of your own assignment.")
        
        acc = attrs.get("location_accuracy_m")
        if acc is not None and acc > 30:
            raise serializers.ValidationError({"location_accuracy_m": "GPS accuracy must be ≤ 30 meters."})

        lat = attrs.get("latitude")
        lng = attrs.get("longitude")
        if (lat is None) ^ (lng is None):
            raise serializers.ValidationError("Both latitude and longitude are required together.")

        return attrs

    def create(self, validated_data):
        # timestamp تلقائي 
        validated_data["timestamp"] = timezone.now()
        return super().create(validated_data)


# قراءات (عرض كأنه حالات توصيلات للسائق) 
class AssignmentListItemSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver.user.name", read_only=True)
    shipment_name = serializers.CharField(source="shipment.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = Assignment
        fields = ["id", "shipment", "shipment_name", "driver", "driver_name",
                  "customer", "warehouse", "warehouse_name",
                  "current_status", "assigned_at"]
        read_only_fields = fields

