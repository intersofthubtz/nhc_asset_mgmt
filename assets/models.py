from django.db import models
from django.conf import settings

class Asset(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    CATEGORY_CHOICES = [
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('printer', 'Printer'),
        ('projector', 'Projector'),
        ('furniture', 'Furniture'),
        # Add more as needed
    ]

    # Use CATEGORY_CHOICES for asset_name
    asset_name = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='laptop'
    )  
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=150, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=150, unique=True, blank=True, null=True)
    specification = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    asset_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    purchase_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_name} ({self.model})"


