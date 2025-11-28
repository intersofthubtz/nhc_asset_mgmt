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



# class Log(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
#     action = models.CharField(max_length=255)
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     related_asset = models.ForeignKey('assets.Asset', null=True, blank=True, on_delete=models.SET_NULL)
#     related_request = models.ForeignKey('assets.AssetRequest', null=True, blank=True, on_delete=models.SET_NULL)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user} | {self.action} | {self.created_at}"



