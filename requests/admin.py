from django.contrib import admin
from .models import AssetRequest, AssetReturn

@admin.register(AssetRequest)
class AssetRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'asset', 'status', 'request_date', 'return_date', 'approved_by', 'approval_date')
    list_filter = ('status',)
    search_fields = ('user__username', 'asset__asset_name')

@admin.register(AssetReturn)
class AssetReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrow_request', 'returned_date', 'condition_on_return', 'received_by')
    list_filter = ('condition_on_return',)
    search_fields = ('borrow_request__asset__asset_name', 'borrow_request__user__username')
