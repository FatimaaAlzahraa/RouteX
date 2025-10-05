from rest_framework.permissions import BasePermission
from .models import WarehouseManager, Driver

class IsWarehouseManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and WarehouseManager.objects.filter(user=request.user).exists()
        )

class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and Driver.objects.filter(user=request.user).exists()
        )

