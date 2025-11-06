from django.db import models
from accounts.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    table_name = models.CharField(max_length=100)
    record_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
