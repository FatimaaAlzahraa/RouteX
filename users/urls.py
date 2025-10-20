# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, whois

urlpatterns = [
    # login endpoint 
    path("api/login", LoginView.as_view(), name="login"),    
    # token refresh endpoint
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # whois endpoint
    path("api/whois", whois, name="whois"),
]


