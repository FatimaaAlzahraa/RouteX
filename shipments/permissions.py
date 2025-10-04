from rest_framework.permissions import BasePermission
from users.models import CustomUser

class IsWarehouseManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == CustomUser.Roles.WAREHOUSE_MANAGER
        )


class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == CustomUser.Roles.DRIVER
        )
