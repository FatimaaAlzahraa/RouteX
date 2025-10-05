from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Extra", {"fields": ( "phone",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("phone",)}),
    )
    list_display = ("username", "phone", "is_staff", "is_active")
    list_filter  = ("is_staff", "is_active")
    search_fields = ("username", "phone")
    ordering = ("username",)
