# users/serializers.py
from rest_framework import serializers
from users.models import CustomUser
from shipments.models import Driver, WarehouseManager

class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "name", "phone", "role", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data, is_active=True)
        user.set_password(password)
        user.save()

        # اختياري: إنشاء البروفايل حسب الدور
        if user.role == CustomUser.Roles.DRIVER:
            Driver.objects.create(user=user)
        elif user.role == CustomUser.Roles.WAREHOUSE_MANAGER:
            WarehouseManager.objects.create(user=user)

        return user

