from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    # Normal user routes
    path('assets/', views.available_assets, name='available_assets'),
    path('assets/<int:pk>/request/', views.request_asset, name='request_asset'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('my-requests/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    
    
    # Staff routes
    path('manage-requests/', views.staff_manage_requests, name='staff_manage_requests'),
    path('manage-request/<int:pk>/<str:action>/', views.update_request_status, name='update_request_status'),
    path('manage-returns/', views.staff_manage_returns, name='staff_manage_returns'),
    path('mark-returned/<int:req_id>/', views.staff_mark_returned, name='staff_mark_returned'),
    path('update-return-condition/<int:return_id>/', views.staff_update_return_condition, name='staff_update_return_condition'),
    
    # Admin routes
    path('admin/manage-requests/', views.admin_manage_requests, name='admin_manage_requests'),
    path('admin/manage-request/<int:pk>/<str:action>/', views.admin_update_request_status, name='admin_update_request_status'),
    path('admin/manage-returns/', views.admin_manage_returns, name='admin_manage_returns'),
    path('admin/mark-returned/<int:req_id>/', views.admin_mark_returned, name='admin_mark_returned'),
    path('admin/update-return-condition/<int:return_id>/', views.admin_update_return_condition, name='admin_update_return_condition'),
    
    
]
