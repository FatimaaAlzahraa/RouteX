from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed

class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        role = "manager" if hasattr(user, "warehouse_manager_profile") else (
               "driver"  if hasattr(user, "driver_profile") else None)
        token["role"] = role
        return token

    def validate(self, attrs):
        request = self.context["request"]
        phone = (request.data.get("phone") or "").strip()
        if not phone:
            raise AuthenticationFailed("phone is required.", code="phone_required")

        data = super().validate(attrs)           # يشيك username/password
        user = self.user
        if (getattr(user, "phone", "") or "").strip() != phone:
            raise AuthenticationFailed("invalid phone for this user.", code="invalid_phone")

        role = "manager" if hasattr(user, "warehouse_manager_profile") else (
               "driver"  if hasattr(user, "driver_profile") else None)

        data.update({"role": role, "username": user.username, "phone": phone})
        return data

class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer
