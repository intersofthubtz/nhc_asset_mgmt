from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    # Normal user routes
    # path('assets/', views.available_assets, name='available_assets'),
    # path('assets/<int:pk>/request/', views.request_asset, name='request_asset'),
    
    path('make-request/', views.make_request, name='make_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('my-requests/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    
    # Staff routes
    path('manage-requests/', views.staff_manage_requests, name='staff_manage_requests'),
    path('manage-request/<int:pk>/<str:action>/', views.update_request_status, name='update_request_status'),
    path('assign-asset/<int:pk>/', views.assign_asset, name='assign_asset'),
    path('get-request-details/<int:pk>/', views.staff_request_details, name='staff_get_request_details'),
    
    path('manage-returns/', views.staff_manage_returns, name='staff_manage_returns'),
    path('mark-returned/<int:req_id>/', views.staff_mark_returned, name='staff_mark_returned'),
    path('return-detail/<int:return_id>/', views.staff_return_detail, name='staff_return_detail'),
    
    # Admin routes
    path('admin/manage-requests/', views.admin_manage_requests, name='admin_manage_requests'),
    path('admin/manage-request/<int:pk>/<str:action>/', views.admin_update_request_status, name='admin_update_request_status'),
    path('admin/assign-asset/<int:pk>/', views.assign_asset, name='assign_asset'),
    path('admin/get-request-details/<int:pk>/', views.admin_request_details, name='admin_get_request_details'),
    
    path('admin/manage-returns/', views.admin_manage_returns, name='admin_manage_returns'),
    path('admin/mark-returned/<int:req_id>/', views.admin_mark_returned, name='admin_mark_returned'),
    path('admin/return-detail/<int:return_id>/', views.admin_return_detail, name='admin_return_detail'),

]
