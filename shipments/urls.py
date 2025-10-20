from django.urls import path
from shipments.views import (
    ShipmentCreateView, ShipmentDetailView,
    DriverShipmentsList,
    StatusUpdateCreateView, WarehouseListCreateView, WarehouseDetailView, CustomerListCreateView,
    ShipmentsListView, AutocompleteShipmentsView,AutocompleteCustomersView,DriverStatusView,
    CustomerDetailView,CustomerAddressesView, ProductListCreateView, ProductDetailView,
)
urlpatterns = [

    # products list/create/update/detete (warehouse manager only) 
    path("api/products", ProductListCreateView.as_view(), name="product-list-create"),
    path("api/products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),

    # shimpents create/detail/update/delete (warehouse manager only)
    path("api/shipments", ShipmentCreateView.as_view(), name="shipment-create"),
    path("api/shipments/<int:pk>", ShipmentDetailView.as_view(), name="shipment-detail"),


    # search shipments for autocomplete
    path("api/autocomplete/shipments", AutocompleteShipmentsView.as_view(), name="ac-shipments"),


    #  manage customers (list/create, detail/update) where warehouse manager only
    path("api/customers", CustomerListCreateView.as_view(), name="customer-list-create"),
    path("api/customers/<int:pk>", CustomerDetailView.as_view(), name="customer-detail"),
    # list customer addresses
    path("customers/<int:pk>/addresses", CustomerAddressesView.as_view(), name="customer-addresses"),
    # search customers for autocomplete
    path("api/autocomplete/customers", AutocompleteCustomersView.as_view(), name="ac-customers"),



    # manage warehouses (list/create, detail/update)
    path("api/warehouses", WarehouseListCreateView.as_view(), name="warehouse-list-create"),
    path("api/warehouses/<int:pk>", WarehouseDetailView.as_view(), name="warehouse-detail"),


    #  list shipments for warehouse manager
    path("api/shipments/manager", ShipmentsListView.as_view(), name="shipments-list"),

    # list driver status for warehouse manager
    path("api/drivers", DriverStatusView.as_view({"get": "list"}), name="driver-status-list"),


    # liste for driver profile
    path("api/shipments/driver", DriverShipmentsList.as_view(), name="driver-shipments"),
    # update driver status
    path("api/status-updates", StatusUpdateCreateView.as_view(), name="statusupdate-create"),
    
]
