from django.db import models
from assets.models import Asset

class AssetMaintenance(models.Model):
    TYPE_CHOICES = [
        ('repair', 'Repair'),
        ('service', 'Service'),
        ('upgrade', 'Upgrade')
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    maintenance_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='service')
    description = models.TextField(blank=True, null=True)
    maintenance_date = models.DateField()
    performed_by = models.CharField(max_length=150, blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
