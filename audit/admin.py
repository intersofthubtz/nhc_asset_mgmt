from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'table_name', 'record_id', 'timestamp')
    list_filter = ('table_name',)
    search_fields = ('action', 'user__username', 'table_name')
