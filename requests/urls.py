from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    
    # Normal user routes
    path('dashboard/', views.normal_dashboard, name='normal_dashboard'),
    path('assets/', views.available_assets, name='available_assets'),
    path('assets/<int:pk>/request/', views.request_asset, name='request_asset'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('my-requests/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    
    # Staff routes
    path('staff/manage-requests/', views.staff_manage_requests, name='staff_manage_requests'),
    path('staff/request/<int:pk>/<str:action>/', views.update_request_status, name='update_request_status'),

    path('staff/manage-returns/', views.staff_manage_returns, name='staff_manage_returns'),
    path('staff/mark-returned/<int:req_id>/', views.staff_mark_returned, name='staff_mark_returned'),
    path('staff/update-return-condition/<int:return_id>/', views.staff_update_return_condition, name='staff_update_return_condition'),


]
