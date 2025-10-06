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
    customer_address = forms.ChoiceField(
        required=False,
        choices=[("", "— اختر العميل أولاً —")],
        label="Customer address",
    )

    class Meta:
        model = Shipment
        fields = "__all__"

    class Media:
        # سكريبت اختياري لو بتستخدميه
        js = ("admin/js/jquery.init.js", "shipments/auto_submit_customer.js")

    def _get_customer(self):
        """
        نحاول تحديد العميل الحالي بترتيب:
        1) instance (لو بنعدّل وكان فيه عميل)
        2) initial['customer'] (من get_changeform_initial_data)
        3) POST self.data['customer']
        4) GET request.GET['customer'] (لما نغيّر العميل في شاشة change ويعمل reload)
        """
        # 1) تعديل سجل موجود وله عميل
        if self.instance and self.instance.pk and self.instance.customer_id:
            return self.instance.customer

        # 2) من initial (add view أو من get_changeform_initial_data)
        cid = self.initial.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None

        # 3) بعد POST
        cid = self.data.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None

        # 4) من GET في صفحة change (نحقن request داخل الفورم من الـ admin)
        req = getattr(self, "_request", None)
        if req:
            cid = req.GET.get("customer")
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

        # اضبط قائمة الاختيارات
        if addresses:
            self.fields["customer_address"].choices = [("", "---------")] + [(a, a) for a in addresses]
            # لو عنوان واحد—هنملاه تلقائيًا لو المستخدم ما اختارش حاجة
            if len(addresses) == 1:
                self.fields["customer_address"].initial = addresses[0]
        else:
            # لا عناوين / لا عميل
            self.fields["customer_address"].choices = [("", "— اختر العميل أولاً —")]

    def clean(self):
        cleaned = super().clean()
        cust = cleaned.get("customer")
        addr = (cleaned.get("customer_address") or "").strip()

        # 1) بدون عميل: العنوان يُتجاهل
        if not cust:
            cleaned["customer_address"] = None
            return cleaned

        # 2) مع وجود عميل — جهّز قائمة المسموح
        allowed = []
        for a in (cust.address, getattr(cust, "address2", ""), getattr(cust, "address3", "")):
            a = (a or "").strip()
            if a and a not in allowed:
                allowed.append(a)

        # 2.a لا يوجد عناوين → امنعي الحفظ
        if not allowed:
            self.add_error("customer", "العميل المحدد ليس له أي عناوين محفوظة.")
            self.add_error("customer_address", "لا يمكن حفظ الشحنة بدون عنوان للعميل.")
            return cleaned

        # 2.b عنوان واحد → املأه تلقائيًا إذا لم يُحدَّد
        if len(allowed) == 1 and not addr:
            cleaned["customer_address"] = allowed[0]
            return cleaned

        # 2.c أكثر من عنوان → مطلوب اختيار واحد من القائمة
        if not addr:
            self.add_error("customer_address", "الرجاء اختيار عنوان للعميل.")
            return cleaned

        if addr not in allowed:
            self.add_error("customer_address", "العنوان يجب أن يكون من عناوين العميل المحفوظة.")
            return cleaned

        return cleaned


# =========================
# Shipment Admin
# =========================
@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    form = ShipmentAdminForm
    autocomplete_fields = ("warehouse", "driver", "customer")

    list_display = (
        "id", "warehouse", "driver", "customer",
        "customer_address", "current_status", "created_at",
    )
    list_filter = ("warehouse", "current_status")
    search_fields = ("id", "warehouse__name", "warehouse__location", "customer__name", "customer_address")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        """
        لو جالنا ?customer=<id> في URL (من onchange بالـ JS أو من الكود)
        نمرره للـ initial عشان الفورم يبني قائمة العناوين فورًا.
        """
        initial = super().get_changeform_initial_data(request)
        cid = request.GET.get("customer")
        if cid:
            initial["customer"] = cid
        return initial

    def get_form(self, request, obj=None, **kwargs):
        """
        1) نحقن request داخل الفورم (عشان يقرأ GET في صفحة change).
        2) نضيف onchange للـ customer عشان يعمل reload ويظهر العناوين فورًا.
        """
        BaseForm = super().get_form(request, obj, **kwargs)

        class RequestAwareForm(BaseForm):
            def __init__(self, *args, **kw):
                super().__init__(*args, **kw)
                self._request = request  # يقرأه _get_customer()

        # اجعل Select العميل يعمل reload عند التغيير (add/change)
        if "customer" in BaseForm.base_fields:
            BaseForm.base_fields["customer"].widget.attrs["onchange"] = (
                "var v=this.value||'';"
                "var url=new URL(window.location.href);"
                "url.searchParams.set('customer', v);"
                "window.location.href=url.toString();"
            )
        return RequestAwareForm




@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ["shipment"]
    list_display = ("shipment", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("shipment__id", "shipment__driver__user__username", "shipment__driver__user__phone")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

