from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


#ROOt Users Account
class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        DRIVER = "DRIVER", "Driver"
        WAREHOUSE_MANAGER = "WAREHOUSE_MANAGER", "Warehouse manager"

    name  = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    role  = models.CharField(max_length=20, choices=Roles.choices, db_index=True)

    def __str__(self):
        return self.name

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
    
#3- Warehouse
class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    manager = models.ForeignKey(
        WarehouseManager, on_delete=models.PROTECT, related_name="warehouses"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["location"]),
        ]
    def __str__(self):
        return self.name

#4- Customer
class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return self.name


# 5- Shipment 
class Shipment(models.Model):
    name = models.CharField(max_length=255)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="shipments"
    )
    shipment_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"Shipment#{self.pk}"



# Shipment Status Choices
class ShipmentStatus(models.TextChoices):
    ASSIGNED = "ASSIGNED", "Assigned"
    PICKED_UP = "PICKED_UP", "Picked up"
    IN_TRANSIT = "IN_TRANSIT", "In transit"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELLED = "CANCELLED", "Cancelled"


# Assignment
class Assignment(models.Model):
    shipment = models.ForeignKey(
        Shipment, on_delete=models.CASCADE, related_name="assignment"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT, related_name="assignments"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="assignments"
    )
    warehouse= models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="assignments",
        help_text="المكان/الفرع الذي ينطلق منه السائق أو يستلم منه."
    )

    notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    current_status = models.CharField(choices=ShipmentStatus.choices, default=ShipmentStatus.ASSIGNED, max_length=20, db_index=True, editable=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["assigned_at"]),
            models.Index(fields=["driver"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["warehouse"]),
            models.Index(fields=["current_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["shipment", "driver"],
                name="uniq_assignment_per_shipment_driver"
            )
        ]
        
    def __str__(self):
       return f"Assign {self.shipment} -> {self.driver} @ {self.warehouse}"


# StatusUpdate (تتبع الحالة)
class StatusUpdate(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="status_updates"
    )
    status = models.CharField(max_length=20, choices=ShipmentStatus.choices, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    note = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["status", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.assignment.shipment} -> {self.status} @ {self.timestamp:%Y-%m-%d %H:%M}"


# Signals: مزامنة حالة الـ Assignment مع أحدث StatusUpdate
@receiver(post_save, sender=StatusUpdate)
def sync_assignment_status(sender, instance: StatusUpdate, created, **kwargs):
    if created:
        Assignment.objects.filter(pk=instance.assignment_id).update(
            current_status=instance.status
        )