from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")

    @property
    def is_admin(self):
        # superuser created with createsuperuser is also treated as admin
        return self.role == "admin" or self.is_superuser

    def __str__(self):
        return self.username
