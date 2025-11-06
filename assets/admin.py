from django.contrib import admin
from .models import AssetCategory, Asset

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'asset_name', 'category', 'status', 'asset_condition', 'assigned_to', 'purchase_date')
    list_filter = ('status', 'asset_condition', 'category')
    search_fields = ('asset_code', 'asset_name', 'serial_number', 'barcode')
