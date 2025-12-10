from django.contrib import admin
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'asset_category',
        'model',
        'status',
        'asset_condition',
        'created_by',
        'created_at'
    )
    list_filter = ('status', 'asset_condition', 'asset_category')
    search_fields = ('asset_category', 'model', 'serial_number', 'barcode')
