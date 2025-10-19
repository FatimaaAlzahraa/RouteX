from django.urls import path
from shipments.views import (
    ShipmentCreateView, ShipmentDetailView,
    DriverShipmentsList,
    StatusUpdateCreateView, WarehouseListCreateView, WarehouseDetailView, CustomerListCreateView,
    ShipmentsListView, AutocompleteShipmentsView,AutocompleteCustomersView,DriverStatusView,
    CustomerDetailView,CustomerAddressesView, ProductListCreateView, ProductDetailView,
)
urlpatterns = [

    # products (قائمة، إنشاء، تعديل، حذف، تفاصيل) (للإدارة فقط)
    path("api/products", ProductListCreateView.as_view(), name="product-list-create"),
    path("api/products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),

    # Shipments (إنشاء، تعديل، حذف، تفاصيل) (للإدارة فقط)
    path("api/shipments", ShipmentCreateView.as_view(), name="shipment-create"),
    path("api/shipments/<int:pk>", ShipmentDetailView.as_view(), name="shipment-detail"),


    # بحث بالاقتراحات الفورية للشحنات 
    path("api/autocomplete/shipments", AutocompleteShipmentsView.as_view(), name="ac-shipments"),


    #  ادارة العملاء (قائمة/انشاء /تعديل/حذف/تفاصيل) (للإدارة فقط)
    path("api/customers", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("api/customers/<int:pk>", CustomerDetailView.as_view(), name="customer-detail"),
    # قائمة عناوين العميل
    path("customers/<int:pk>/addresses", CustomerAddressesView.as_view(), name="customer-addresses"),
    # بحث بالاقتراحات الفورية للعملاء
    path("api/autocomplete/customers", AutocompleteCustomersView.as_view(), name="ac-customers"),



    # إدارة المستودع ( انشاء/تعديل/حذف/تفاصيل) (للإدارة فقط)
    path("api/warehouses", WarehouseListCreateView.as_view(), name="warehouse-list-create"),
    path("api/warehouses/<int:pk>", WarehouseDetailView.as_view(), name="warehouse-detail"),


    #  قائمة للمدير ومزامنة الشحنات
    path("api/shipments/manager", ShipmentsListView.as_view(), name="shipments-list"),

    # قائمة السائق (للإدارة فقط)
    path("api/drivers", DriverStatusView.as_view({"get": "list"}), name="driver-status-list"),
    # path("api/drivers/status/<int:pk>", DriverStatusView.as_view({"get": "retrieve"}), name="driver-status-detail"),


    # قائمة الشحنات للسائق
    path("api/shipments/driver", DriverShipmentsList.as_view(), name="driver-shipments"),
    # تحديث الحالة من السائق
    path("api/status-updates", StatusUpdateCreateView.as_view(), name="statusupdate-create"),
    
]
