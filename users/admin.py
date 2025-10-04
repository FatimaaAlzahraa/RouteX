from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,

)
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
    search_fields = ("username", "name", "phone", "role")
    ordering = ("username",)
