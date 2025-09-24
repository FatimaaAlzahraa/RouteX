from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Driver, WarehouseManager,
    Warehouse, Customer, Shipment, Assignment, StatusUpdate, ShipmentStatus
)

# =========================
# CustomUser
# =========================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Extra", {"fields": ("name", "phone", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("name", "phone", "role")}),
    )
    list_display = ("username", "name", "phone", "role", "is_staff", "is_active")
    list_filter  = ("role", "is_staff", "is_active")
    search_fields = ("username", "name", "phone", "email")
    ordering = ("username",)


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
    autocomplete_fields = ["manager"]
    list_display = ("name", "location", "manager_name", "created_at")
    list_filter = ("location",)
    search_fields = ("name", "location", "manager__user__name", "manager__user__username", "manager__user__phone")
    date_hierarchy = "created_at"

    def manager_name(self, obj): return obj.manager.user.name
    manager_name.short_description = "Manager"


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
    list_display = ("name", "warehouse", "created_at")
    list_filter = ("warehouse",)
    search_fields = ("name", "warehouse__name", "warehouse__location")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# =========================
# StatusUpdate Inline (داخل Assignment)
# =========================
class StatusUpdateInline(admin.TabularInline):
    model = StatusUpdate
    extra = 0
    fields = ("status", "timestamp", "note", "attachment_url")
    readonly_fields = ()
    ordering = ("-timestamp",)


# =========================
# Assignment
# =========================
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    inlines = [StatusUpdateInline]
    autocomplete_fields = ["shipment", "driver", "customer", "warehouse"]
    list_display = ("shipment", "driver_name", "customer", "warehouse", "current_status", "assigned_at")
    list_filter = ("current_status", "warehouse")
    search_fields = (
        "shipment__name",
        "driver__user__name", "driver__user__username", "driver__user__phone",
        "customer__name", "customer__phone",
        "warehouse__name", "warehouse__location",
    )
    date_hierarchy = "assigned_at"
    readonly_fields = ("current_status",)
    ordering = ("-assigned_at",)

    def driver_name(self, obj): return obj.driver.user.name
    driver_name.short_description = "Driver"


# =========================
# StatusUpdate
# =========================
@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ["assignment"]
    list_display = ("assignment", "status", "timestamp")
    list_filter = ("status",)
    search_fields = (
        "assignment__shipment__name",
        "assignment__driver__user__name",
        "assignment__driver__user__username",
    )
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)


