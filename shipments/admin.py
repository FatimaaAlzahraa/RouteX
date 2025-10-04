from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Driver, WarehouseManager,
    Warehouse, Customer, Shipment, StatusUpdate, ShipmentStatus
)



# =========================
# Driver
# =========================
class DriverAdminForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["user", "is_active"]

    def clean_user(self):
        u = self.cleaned_data["user"]
        # تأكيد إن اليوزر دوره DRIVER
        if getattr(u, "role", None) != CustomUser.Roles.DRIVER:
            raise forms.ValidationError("Selected user must have role = DRIVER.")
        return u

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    form = DriverAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_name", "user_username", "user_phone", "is_active")
    search_fields = ("user__username", "user__name", "user__phone")
    list_filter = ("is_active",)

    def user_name(self, obj): return obj.user.name
    user_name.short_description = "Name"

    def user_username(self, obj): return obj.user.username
    user_username.short_description = "Username"

    def user_phone(self, obj): return obj.user.phone
    user_phone.short_description = "Phone"


# =========================
# Warehouse Manager
# =========================
class WarehouseManagerAdminForm(forms.ModelForm):
    class Meta:
        model = WarehouseManager
        fields = ["user"]

    def clean_user(self):
        u = self.cleaned_data["user"]
        if getattr(u, "role", None) != CustomUser.Roles.WAREHOUSE_MANAGER:
            raise forms.ValidationError("Selected user must have role = WAREHOUSE_MANAGER.")
        return u

@admin.register(WarehouseManager)
class WarehouseManagerAdmin(admin.ModelAdmin):
    form = WarehouseManagerAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_name", "user_username", "user_phone")
    search_fields = ("user__username", "user__name", "user__phone")

    def user_name(self, obj): return obj.user.name
    def user_username(self, obj): return obj.user.username
    def user_phone(self, obj): return obj.user.phone


# =========================
# Warehouse
# =========================
@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at")
    list_filter = ("location",)
    search_fields = ("name", "location")
    date_hierarchy = "created_at"



# =========================
# Customer
# =========================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "address")
    search_fields = ("name", "phone")
    list_per_page = 50


# =========================
# Shipment
# =========================
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    autocomplete_fields = ["warehouse"]
    list_display = ("id", "warehouse", "driver", "customer", "current_status", "created_at")  # قم بتعديل هذا الحقل
    list_filter = ("warehouse", "current_status")
    search_fields = ("id", "warehouse__name", "warehouse__location")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)



# =========================
# StatusUpdate
# =========================
@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ["shipment"]  # تعديل assignment إلى shipment
    list_display = ("shipment", "status", "timestamp")  # تعديل assignment إلى shipment
    list_filter = ("status",)
    search_fields = ("shipment__id", "shipment__driver__user__name")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)




