from django.contrib import admin
from django import forms
from .models import Driver, WarehouseManager, Warehouse, Customer, Shipment, StatusUpdate




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

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "address")
    search_fields = ("name", "phone")
    list_per_page = 50




class ShipmentAdminForm(forms.ModelForm):
    # نعرضه كـ ChoiceField — هنملأ الاختيارات في __init__
    customer_address = forms.ChoiceField(
        required=True,
        choices=[("", "— اختر العميل أولاً —")],
        label="Customer address",
    )

    class Meta:
        model = Shipment
        fields = "__all__"

    # حمّلي ملف JS الخارجي (مش inline)
    class Media:
        js = ("admin/js/jquery.init.js", "shipments/auto_submit_customer.js")

    def _get_customer(self):
        # 1) لو بنعدّل سجل موجود
        if self.instance and self.instance.pk and self.instance.customer_id:
            return self.instance.customer

        # 2) لو جايه من GET ?customer=...
        cid = self.initial.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None

        # 3) لو بعد POST
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
            for a in (cust.address, cust.address2, cust.address3):
                if a:
                    a = a.strip()
                    if a and a not in addresses:
                        addresses.append(a)

        if addresses:
            self.fields["customer_address"].choices = [("", "---------")] + [(a, a) for a in addresses]
            # لو عنوان واحد فقط—املأه تلقائيًا
            if len(addresses) == 1:
                self.fields["customer_address"].initial = addresses[0]
            # مساعدة مرئية
            self.fields["customer"].help_text = "Addresses: " + ", ".join(addresses)
        else:
            self.fields["customer_address"].choices = [("", "— اختر العميل أولاً —")]

    def clean(self):
        cleaned = super().clean()
        cust = cleaned.get("customer")
        addr = (cleaned.get("customer_address") or "").strip()

        if not cust:
            raise forms.ValidationError("اختر العميل أولًا.")

        valid = []
        for a in (cust.address, cust.address2, cust.address3):
            if a:
                a = a.strip()
                if a and a not in valid:
                    valid.append(a)

        if not valid:
            raise forms.ValidationError("العميل لا يملك عناوين محفوظة.")

        if len(valid) == 1 and not addr:
            cleaned["customer_address"] = valid[0]
            return cleaned

        if addr not in valid:
            raise forms.ValidationError("يجب اختيار عنوان من عناوين العميل.")
        return cleaned

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    # نربط الـ ModelForm اللي بيطلع قائمة عناوين العميل
    form = ShipmentAdminForm

    # تسهيل الاختيار في الأدمن
    autocomplete_fields = ("warehouse", "driver", "customer")

    # تنظيم عرض الشحنات
    list_display = ("id", "warehouse", "driver", "customer",
                    "customer_address", "current_status", "created_at")
    list_filter = ("warehouse", "current_status")
    search_fields = ("id", "warehouse__name", "warehouse__location",
                     "customer__name", "customer_address")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    # علشان لما الـ JS يضيف ?customer=<id> في الـ URL
    # نمررها للـ form.initial → فيُعاد بناء قائمة العناوين فورًا
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

