
# project/urls.py أو appRouteX/urls.py (اختار واحد)
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from appRouteX.views import (
    ShipmentCreateView, AssignmentCreateView,
    ManagerAssignmentsList, DriverAssignmentsList,
    StatusUpdateCreateView, ShipmentDetailView, AssignmentDetailView,WarehouseCreateView, WarehouseDetailView, CustomerCreateView,
)

urlpatterns = [
    # Auth (JWT)
    path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),

    # Shipments (إنشاء، تعديل، حذف، تفاصيل)
    path("api/shipments", ShipmentCreateView.as_view(), name="shipment-create"),
    path("api/shipments/<int:pk>", ShipmentDetailView.as_view(), name="shipment-detail"),

    # Assignments (إنشاء، تعديل، حذف، تفاصيل)
    path("api/assignments", AssignmentCreateView.as_view(), name="assignment-create"),
    path("api/assignments/<int:pk>", AssignmentDetailView.as_view(), name="assignment-detail"),
    #قائمة التعيينات للمدير والسائق
    path("api/assignments/manager", ManagerAssignmentsList.as_view(), name="manager-assignments"),
    path("api/assignments/driver", DriverAssignmentsList.as_view(), name="driver-assignments"),

    path("api/warehouses", WarehouseCreateView.as_view(), name="warehouse-create"),
    path("api/warehouses/<int:pk>", WarehouseDetailView.as_view(), name="warehouse-detail"),

    # Customers (مدير فقط)
    path("api/customers", CustomerCreateView.as_view(), name="customer-create"),

    # تحديث الحالة من السائق
    path("api/status-updates", StatusUpdateCreateView.as_view(), name="statusupdate-create"),
]
