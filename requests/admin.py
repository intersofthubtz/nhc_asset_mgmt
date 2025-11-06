from django.contrib import admin
from .models import BorrowRequest, AssetReturn

@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'asset', 'status', 'request_date', 'start_date', 'end_date', 'approved_by', 'approval_date')
    list_filter = ('status',)
    search_fields = ('user__username', 'asset__asset_name')

@admin.register(AssetReturn)
class AssetReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrow_request', 'returned_date', 'condition_on_return', 'received_by')
    list_filter = ('condition_on_return',)
    search_fields = ('borrow_request__asset__asset_name', 'borrow_request__user__username')
