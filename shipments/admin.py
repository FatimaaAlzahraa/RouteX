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
            raise forms.ValidationError("This user already has a Warehouse Manager profile.")
        return u

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    form = DriverAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_username", "user_phone", "is_active")
    search_fields = ("user__username", "user__phone")  # tuple صحيحة
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
            raise forms.ValidationError("This user already has a Driver profile.")
        return u

@admin.register(WarehouseManager)
class WarehouseManagerAdmin(admin.ModelAdmin):
    form = WarehouseManagerAdminForm
    autocomplete_fields = ["user"]
    list_display = ("id", "user_username", "user_phone")
    search_fields = ("user__username", "user__phone")  # كانت سبب الخطأ — خليه tuple
    # لو عندك عنصر واحد بس، اكتبيه ("user__username",) بالفاصلة

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


# =============== Shipment Admin ===============
class ShipmentAdminForm(forms.ModelForm):
    # نخليها ChoiceField عشان نتحكم في القائمة
    customer_address = forms.ChoiceField(
        required=False,   # هنخليه required=True لما يبقى في عميل
        choices=[],
        label="Customer address",
    )

    class Meta:
        model = Shipment
        fields = "__all__"

    def _get_customer(self):
        # حالة التعديل
        if self.instance and self.instance.pk and self.instance.customer_id:
            return self.instance.customer
        # حالة الإضافة/إعادة التحميل: ناخد initial اللي جاي من admin (GET)
        cid = self.initial.get("customer")
        if cid:
            try:
                return Customer.objects.get(pk=cid)
            except Customer.DoesNotExist:
                return None
        # fallback: لو في POST (rare هنا لأننا عاملين reload بـ GET)
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
        choices = [("", "---------")]
        if cust:
            addresses = [cust.address, getattr(cust, "address2", None), getattr(cust, "address3", None)]
            addresses = [a for a in addresses if a]
            choices += [(a, a) for a in addresses]
            # بما إن في عميل، يبقى لازم يختار عنوان حتى لو واحد
            self.fields["customer_address"].required = True

            # مساعدة لطيفة
            shown = ", ".join(addresses)
            self.fields["customer"].help_text = f"Addresses: {shown or 'No addresses'}"
        else:
            self.fields["customer_address"].required = False

        self.fields["customer_address"].choices = choices

    def clean(self):
        cleaned = super().clean()
        cust = self._get_customer()
        addr = (cleaned.get("customer_address") or "").strip()

        if not cust:
            # لو مفيش عميل خالص -> خليه None
            cleaned["customer_address"] = None
            return cleaned

        allowed = [a for a in [cust.address, cust.address2, cust.address3] if a]

        if not allowed:
            self.add_error("customer", "Selected customer has no saved addresses.")
            return cleaned

        # إلزام الاختيار حتى لو عنوان واحد
        if not addr:
            self.add_error("customer_address", "Please choose one of the customer's addresses.")
            return cleaned

        if addr not in allowed:
            self.add_error("customer_address", "Address must be one of the customer's saved addresses.")
        return cleaned


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    form = ShipmentAdminForm
    autocomplete_fields = ["warehouse", "driver", "customer"]
    list_display = ("id", "warehouse", "driver", "customer", "customer_address", "current_status", "created_at")
    list_filter = ("warehouse", "current_status")
    search_fields = ("id", "warehouse__name", "warehouse__location", "customer__name", "customer_address")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        """
        ناخد customer من الـ GET ونمرّره كـ initial للفورم
        عشان الفورم يبني قائمة العناوين على طول.
        """
        initial = super().get_changeform_initial_data(request)
        cid = request.GET.get("customer")
        if cid:
            initial["customer"] = cid
        return initial

    def get_form(self, request, obj=None, **kwargs):
        """
        نزود onchange على حقل customer
        يخلي الصفحة تعيد التحميل بـ ?customer=<id> بدون أي JSON أو ملفات static.
        """
        form = super().get_form(request, obj, **kwargs)
        if "customer" in form.base_fields:
            # NB: ده حقل الـ input المخفي/الـ select نفسه—بينجح مع select2 برضه
            form.base_fields["customer"].widget.attrs["onchange"] = (
                "var v=this.value||'';"
                "var url=new URL(window.location.href);"
                "url.searchParams.set('customer', v);"
                "window.location.href=url.toString();"
            )
        return form



@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ["shipment"]
    list_display = ("shipment", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("shipment__id", "shipment__driver__user__username", "shipment__driver__user__phone")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
