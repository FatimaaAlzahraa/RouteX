# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, whois

urlpatterns = [
    path("api/login", LoginView.as_view(), name="login"),     # ← هنا التعديل
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/whois", whois, name="whois"),
]


# # users/urls.py
# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
# from .jwt import PhoneTokenObtainPairView      # <— بدّلنا الاستيراد
# from .views import whoami

# urlpatterns = [
#     path("api/login/", PhoneTokenObtainPairView.as_view(), name="login_with_phone"),
#     path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
#     path("api/whoami/", whoami, name="whoami"),  # اختياري
# ]

