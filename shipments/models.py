from django.db import models
from users.models import CustomUser
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


# 1- Driver
class Driver(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"role": CustomUser.Roles.DRIVER},
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.user.name

class WarehouseManager(models.Model):  
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="warehouse_manager_profile",
        limit_choices_to={"role": CustomUser.Roles.WAREHOUSE_MANAGER},
    )

    def __str__(self):
        return self.user.name
    
#2- Warehouse
class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["location"]),
        ]
    def __str__(self):
        return self.name

#3- Customer
class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return self.name


# 4- Shipment Status Choices
class ShipmentStatus(models.TextChoices):
    NEW = "NEW", "New"
    ASSIGNED = "ASSIGNED", "Assigned"
    PICKED_UP = "PICKED_UP", "Picked up"
    IN_TRANSIT = "IN_TRANSIT", "In transit"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELLED = "CANCELLED", "Cancelled"


# 5- Shipment 
class Shipment(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="shipments"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT, related_name="shipments", null=True, blank=True
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="shipments", null=True, blank=True
    )
    shipment_details = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(default=timezone.now)  # تم إضافته من نموذج Assignment
    current_status = models.CharField(max_length=20, default=ShipmentStatus.NEW, choices=ShipmentStatus.choices, db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipment#{self.pk} - {self.customer.name if self.customer else 'No Customer'}"




# StatusUpdate 
class StatusUpdate(models.Model):
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="status_updates"
    )
    status = models.CharField(max_length=20, choices=ShipmentStatus.choices, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    note = models.TextField(blank=True)
    photo = models.ImageField(upload_to="status_photos/", blank=True, null=True)
    location_accuracy_m = models.PositiveIntegerField(null=True, blank=True, help_text="GPS accuracy in meters.")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["status", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.shipment} -> {self.status} @ {self.timestamp:%Y-%m-%d %H:%M}"


