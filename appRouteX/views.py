# appRouteX/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.db.models import Q

from .permissions import IsWarehouseManager, IsDriver
from .models import Shipment, Assignment, StatusUpdate, WarehouseManager, Warehouse, Customer
from .serializers import (
    ShipmentSerializer,
    AssignmentSerializer,
    StatusUpdateSerializer,
    AssignmentListItemSerializer,WarehouseSerializer, CustomerSerializer,
    CustomerLiteSerializer,ShipmentLiteSerializer
)


#Shipments
class ShipmentCreateView(generics.CreateAPIView):
    # المدير بيضيف شحنته في المستودع اللي اختاره
    queryset = Shipment.objects.select_related("warehouse")
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

class AutocompleteShipmentsView(generics.ListAPIView):
    serializer_class = ShipmentLiteSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        # المدير يشوف شحنات مخازنه فقط 
        wm = WarehouseManager.objects.get(user=self.request.user)
        qs = Shipment.objects.filter(warehouse__manager=wm)
        if q:
            qs = qs.filter(Q(name__istartswith=q) | Q(name__icontains=q))
        return qs.order_by("name")[:20]


# تفاصيل، تعديل، حذف شحنة
class ShipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]
    queryset = Shipment.objects.select_related("warehouse", "warehouse__manager__user")

    def get_queryset(self):
        try:
            wm = WarehouseManager.objects.get(user=self.request.user)
        except WarehouseManager.DoesNotExist:
            return Shipment.objects.none()
        return self.queryset.filter(warehouse__manager=wm)

class SyncShipmentsView(generics.ListAPIView):
    serializer_class = ShipmentLiteSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

    def list(self, request, *args, **kwargs):
        wm = WarehouseManager.objects.get(user=self.request.user)
        updated_since = request.query_params.get("updated_since")
        qs = Shipment.objects.filter(warehouse__manager=wm)
        if updated_since:
            dt = parse_datetime(updated_since)
            if dt:
                qs = qs.filter(updated_at__gte=dt)
        qs = qs.order_by("updated_at")[:500]
        return Response(self.get_serializer(qs, many=True).data)



#Assignments 
class AssignmentCreateView(generics.CreateAPIView):
   
    # المدير بيضيف تعيين انه بيربط الشحنة بسائق والعميل اللي هيوصل ليه الشحنة 
    # والشحنة لازم تكون من نفس المخزن 
    queryset = (Assignment.objects
                .select_related("shipment", "driver__user", "warehouse", "customer"))
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

# تفاصيل، تعديل، حذف تعيين
class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]
    queryset = (Assignment.objects
                .select_related("shipment__warehouse", "warehouse__manager__user", "driver__user", "customer"))

    def get_queryset(self):
        # يسمح للمدير يشوف/يعدّل/يحذف تعيينات المخازن اللي بيديرها فقط
        try:
            wm = WarehouseManager.objects.get(user=self.request.user)
        except WarehouseManager.DoesNotExist:
            return Assignment.objects.none()
        return self.queryset.filter(warehouse__manager=wm)



class ManagerAssignmentsList(generics.ListAPIView):
    #قائمة التعيينات لكل المخازن التي يديرها المستخدم (Warehouse Manager).
    serializer_class = AssignmentListItemSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

    def get_queryset(self):
        wm = WarehouseManager.objects.select_related("user").get(user=self.request.user)
        return (Assignment.objects
                .select_related("shipment", "driver__user", "warehouse", "customer")
                .filter(warehouse__manager=wm)
                .order_by("-assigned_at"))


class DriverAssignmentsList(generics.ListAPIView):
    # التعيينات الخاصة بالسائق الحالي
    serializer_class = AssignmentListItemSerializer
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self):
        return (Assignment.objects
                .select_related("shipment", "driver__user", "warehouse", "customer")
                .filter(driver__user=self.request.user)
                .order_by("-assigned_at"))
    

class WarehouseCreateView(generics.CreateAPIView):
    queryset = Warehouse.objects.select_related("manager__user")
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]  # مدير فقط

class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]  # مدير فقط
    queryset = Warehouse.objects.select_related("manager__user")

    # المدير يشوف/يعدّل/يحذف مخازنه فقط
    def get_queryset(self):
        try:
            wm = WarehouseManager.objects.get(user=self.request.user)
        except WarehouseManager.DoesNotExist:
            return Warehouse.objects.none()
        return self.queryset.filter(manager=wm)

class CustomerCreateView(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

class AutocompleteCustomersView(generics.ListAPIView):
    serializer_class = CustomerLiteSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        qs = Customer.objects.all()
        if q:
            # يطابق بداية الاسم/التليفون ويقبل احتواء لاحقًا
            qs = qs.filter(Q(name__istartswith=q) | Q(phone__istartswith=q) | Q(name__icontains=q))
        return qs.order_by("name")[:20]  # اقتراحات سريعة

class SyncCustomersView(generics.ListAPIView):
    serializer_class = CustomerLiteSerializer
    permission_classes = [IsAuthenticated, IsWarehouseManager]

    def list(self, request, *args, **kwargs):
        updated_since = request.query_params.get("updated_since")
        qs = Customer.objects.all()
        if updated_since:
            dt = parse_datetime(updated_since)
            if dt:
                qs = qs.filter(updated_at__gte=dt)
        qs = qs.order_by("updated_at")[:500]
        return Response(self.get_serializer(qs, many=True).data)
    
class CustomerQuickAddView(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer  # موجود بالفعل وبيرفض غير المدير. :contentReference[oaicite:12]{index=12}
    permission_classes = [IsAuthenticated, IsWarehouseManager]


# StatusUpdates
class StatusUpdateCreateView(generics.CreateAPIView):
     #يسمح للسائق انه يحدث حالة لتعيينه فقط
    queryset = StatusUpdate.objects.select_related("assignment", "assignment__driver__user")
    serializer_class = StatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsDriver]


class MyStatusUpdatesList(generics.ListAPIView):
    
    #قائمة كل تحديثات الحالة المرتبطة بتعيينات السائق الحالي.
    
    serializer_class = StatusUpdateSerializer  
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self):
        return (StatusUpdate.objects
                .select_related("assignment__shipment", "assignment__driver__user")
                .filter(assignment__driver__user=self.request.user)
                .order_by("-timestamp"))

