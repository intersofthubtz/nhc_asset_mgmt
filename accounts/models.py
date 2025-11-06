from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('normal', 'Normal User'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='normal')

    def save(self, *args, **kwargs):
        # Superusers always have role='admin'
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
