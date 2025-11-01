from django.apps import AppConfig

class AppRouteXConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shipments"   

    def ready(self):
        from . import signals  

