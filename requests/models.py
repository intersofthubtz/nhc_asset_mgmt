from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from assets.models import Asset


class AssetRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_requests')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='asset_requests')
    request_date = models.DateField()
    return_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_asset_requests')
    approval_date = models.DateTimeField(null=True, blank=True)

    def clean(self):
        today = timezone.localdate()
        if self.request_date < today:
            raise ValidationError("Request date cannot be before today.")
        if self.return_date < self.request_date:
            raise ValidationError("Return date cannot be earlier than the request date.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 'approved':
            self.asset.status = 'borrowed'
        elif self.status in ['returned', 'rejected']:
            if not AssetRequest.objects.filter(asset=self.asset, status='approved').exclude(pk=self.pk).exists():
                self.asset.status = 'available'
        self.asset.save()

    def __str__(self):
        return f"{self.user.username} → {self.asset.asset_name} ({self.status})"


class AssetReturn(models.Model):
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]

    borrow_request = models.ForeignKey(AssetRequest, on_delete=models.CASCADE, related_name='returns')
    returned_date = models.DateTimeField(auto_now_add=True)
    condition_on_return = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_returns')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Return: {self.borrow_request.asset.asset_name} by {self.borrow_request.user.username}"

    class Meta:
        ordering = ['-returned_date']
