from django.urls import path
from shipments.views import (
    ShipmentCreateView, ShipmentDetailView,
    DriverShipmentsList,
    StatusUpdateCreateView, WarehouseCreateView, WarehouseDetailView, CustomerCreateView,
    ShipmentsListView, AutocompleteShipmentsView,AutocompleteCustomersView
)

urlpatterns = [
    # Shipments (إنشاء، تعديل، حذف، تفاصيل)
    path("api/shipments", ShipmentCreateView.as_view(), name="shipment-create"),
    path("api/shipments/<int:pk>", ShipmentDetailView.as_view(), name="shipment-detail"),


    # بحث بالاقتراحات الفورية للشحنات
    path("api/autocomplete/shipments", AutocompleteShipmentsView.as_view(), name="ac-shipments"),


    # إضافة عميل جديد (للإدارة فقط)
    path("api/customers", CustomerCreateView.as_view(), name="customer-create"),
    # بحث بالاقتراحات الفورية للعملاء
    path("api/autocomplete/customers", AutocompleteCustomersView.as_view(), name="ac-customers"),



    # إدارة المستودع (إنشاء، تعديل، حذف، تفاصيل) - للمدير فقط
    path("api/warehouses", WarehouseCreateView.as_view(), name="warehouse-create"),
    path("api/warehouses/<int:pk>", WarehouseDetailView.as_view(), name="warehouse-detail"),


    #  قائمة للمدير ومزامنة الشحنات
    path("api/shipments/manager", ShipmentsListView.as_view(), name="shipments-list"),
    


    # قائمة الشحنات للسائق
    path("api/shipments/driver", DriverShipmentsList.as_view(), name="driver-shipments"),
    # تحديث الحالة من السائق
    path("api/status-updates", StatusUpdateCreateView.as_view(), name="statusupdate-create"),
]
