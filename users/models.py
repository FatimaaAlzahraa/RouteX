from django.db import models
from django.contrib.auth.models import AbstractUser


# Custom User Model
class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        DRIVER = "DRIVER", "Driver"
        WAREHOUSE_MANAGER = "WAREHOUSE_MANAGER", "Warehouse manager"

    name  = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    role  = models.CharField(max_length=20, choices=Roles.choices, db_index=True)

    def __str__(self):
        return self.name
