
from django.urls import path
from users.views import loginview
urlpatterns = [
    path("api/login", loginview.as_view(), name="login"),
]
