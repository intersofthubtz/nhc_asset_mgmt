from django.contrib import admin
from .models import Asset

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'model', 'status', 'asset_condition', 'created_by', 'created_at')
    list_filter = ('status', 'asset_condition') 
    search_fields = ('asset_name', 'model', 'serial_number', 'barcode')
