from django.contrib import admin
from .models import AssetMaintenance

@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'maintenance_type', 'maintenance_date', 'performed_by', 'cost')
    list_filter = ('maintenance_type', 'maintenance_date')
    search_fields = ('asset__asset_name', 'performed_by')
