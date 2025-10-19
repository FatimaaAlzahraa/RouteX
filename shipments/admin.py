from django.contrib import admin
from django import forms
from .models import Driver, WarehouseManager, Warehouse,Customer, Shipment, StatusUpdate, Product





class DriverAdminForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["user", "is_active"]

    def clean_user(self):
        u = self.cleaned_data["user"]
        if WarehouseManager.objects.filter(user=u).exists():
            raise forms.ValidationError("This user already has a Driver profile.")
        return u

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    form = DriverAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_username", "user_phone", "is_active")
    search_fields = ("user__username", "user__phone")
    list_filter = ("is_active",)

    def user_username(self, obj): return obj.user.username
    def user_phone(self, obj): return obj.user.phone

class WarehouseManagerAdminForm(forms.ModelForm):
    class Meta:
        model = WarehouseManager
        fields = ["user"]

    def clean_user(self):
        u = self.cleaned_data["user"]
        if Driver.objects.filter(user=u).exists():
            raise forms.ValidationError("This user already has a Warehousing Manager profile.")
        return u

@admin.register(WarehouseManager)
class WarehouseManagerAdmin(admin.ModelAdmin):
    form = WarehouseManagerAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_username", "user_phone")
    search_fields = ("user__username", "user__phone")

    def user_username(self, obj): return obj.user.username
    def user_phone(self, obj): return obj.user.phone

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at")
    list_filter = ("location",)
    search_fields = ("name", "location")
    date_hierarchy = "created_at"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "price", "stock_qty", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "address")
    search_fields = ("name", "phone")
    list_per_page = 50



class ShipmentAdminForm(forms.ModelForm):
    customer_address = forms.ChoiceField(
        required=False,  
        choices=[("", "— اختر العميل أولاً —")],
        label="Customer address",
    )

    class Meta:
        model = Shipment
        fields = "__all__"

    def _get_customer(self):
        if self.instance and self.instance.pk and self.instance.customer_id:
            return self.instance.customer

        cid = self.initial.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None

        cid = self.data.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cust = self._get_customer()
        addresses = []
        if cust:
            for a in (cust.address, getattr(cust, "address2", ""), getattr(cust, "address3", "")):
                a = (a or "").strip()
                if a and a not in addresses:
                    addresses.append(a)

        if addresses:
            self.fields["customer_address"].choices = [("", "choose")] + [(a, a) for a in addresses]
            if len(addresses) == 1:
                # لو عنوان واحد – تلقائيًا املأه
                self.fields["customer_address"].initial = addresses[0]
        else:
            self.fields["customer_address"].choices = [("", "— اختر العميل أولاً —")]

    def clean(self):
        cleaned = super().clean()
        cust = cleaned.get("customer")
        addr = (cleaned.get("customer_address") or "").strip()

        # بدون عميل: تجاهل العنوان
        if not cust:
            cleaned["customer_address"] = None
            return cleaned

        # قائمة العناوين
        allowed = []
        for a in (cust.address, getattr(cust, "address2", ""), getattr(cust, "address3", "")):
            a = (a or "").strip()
            if a and a not in allowed:
                allowed.append(a)

        if not allowed:
            self.add_error("customer", "العميل المحدد ليس له أي عناوين محفوظة.")
            self.add_error("customer_address", "لا يمكن حفظ الشحنة بدون عنوان للعميل.")
            return cleaned

        # عنوان واحد : املأ تلقائيًا إذا كان فارغًا
        if len(allowed) == 1 and not addr:
            cleaned["customer_address"] = allowed[0]
            return cleaned

        # أكثر من عنوان : مطلوب اختيار واحد
        if not addr:
            self.add_error("customer_address", "الرجاء اختيار عنوان للعميل.")
            return cleaned

        if addr not in allowed:
            self.add_error("customer_address", "العنوان يجب أن يكون من عناوين العميل المحفوظة.")
            return cleaned

        cleaned["customer_address"] = addr
        return cleaned


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    form = ShipmentAdminForm
    autocomplete_fields = ("product" , "warehouse", "driver", "customer")

    list_display = ("id", "product","warehouse", "driver", "customer",
                    "customer_address", "current_status", "created_at")
    list_filter = ("warehouse", "current_status")
    search_fields = ("id", "warehouse__name", "warehouse__location",
                     "customer__name", "customer_address","product__name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        cid = request.GET.get("customer")
        if cid:
            initial["customer"] = cid
        return initial




@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ["shipment"]
    list_display = ("shipment", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("shipment__id", "shipment__driver__user__username", "shipment__driver__user__phone")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

