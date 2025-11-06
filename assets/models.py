from django.db import models
from accounts.models import User

class AssetCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired')
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ]

    asset_code = models.CharField(max_length=100, unique=True)
    asset_name = models.CharField(max_length=150)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=150, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=150, unique=True, blank=True, null=True)
    specification = models.TextField(blank=True, null=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    asset_condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    purchase_date = models.DateField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"
