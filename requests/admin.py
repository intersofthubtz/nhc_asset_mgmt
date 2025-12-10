from django.contrib import admin
from .models import AssetRequest, AssetReturn


@admin.register(AssetRequest)
class AssetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset_category', 'status', 'request_date', 'return_date')
    list_filter = ('status', 'asset_category')
    search_fields = ('user__username', 'asset_category')


@admin.register(AssetReturn)
class AssetReturnAdmin(admin.ModelAdmin):
    list_display = ('borrow_request', 'returned_date', 'condition_on_return')
    list_filter = ('condition_on_return',)
