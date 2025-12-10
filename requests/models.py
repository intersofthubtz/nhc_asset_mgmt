from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User


class AssetRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    CATEGORY_CHOICES = [
        ('laptop', 'Laptop'),
        ('projector', 'Projector'),
        ('desktop', 'Desktop'),
    ]

    # Normal User Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_requests')
    asset_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='laptop')
    request_date = models.DateField()
    return_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    # Admin Workflow Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_asset_requests'
    )
    approval_date = models.DateTimeField(null=True, blank=True)

    def clean(self):
        today = timezone.localdate()
        # Prevent NoneType comparisons
        if self.request_date is not None and self.request_date < today:
            raise ValidationError("Request date cannot be before today.")

        if self.request_date is not None and self.return_date is not None:
            if self.return_date < self.request_date:
                raise ValidationError("Return date cannot be earlier than the request date.")

    def __str__(self):
        return f"{self.user.username} → {self.asset_category} ({self.status})"

    class Meta:
        ordering = ['-request_date']


class AssetReturn(models.Model):
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]

    borrow_request = models.ForeignKey(
        AssetRequest,
        on_delete=models.CASCADE,
        related_name='returns'
    )
    returned_date = models.DateTimeField(null=True, blank=True)
    condition_on_return = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_returns'
    )
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Return → {self.borrow_request.asset_category} by {self.borrow_request.user.username}"

    class Meta:
        ordering = ['-returned_date']
