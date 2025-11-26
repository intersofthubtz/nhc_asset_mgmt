from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    #admin
    path('admin/manage-assets/', views.admin_manage_assets, name='admin_manage_assets'),
    
    #staff
    path('manage-assets/', views.staff_manage_assets, name='staff_manage_assets'),
    path('assets/add/', views.add_asset, name='add_asset'),
    path('assets/<int:pk>/edit/', views.edit_asset, name='edit_asset'),
    path('assets/<int:pk>/delete/', views.delete_asset, name='delete_asset'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    
    path('export-report/<str:report_type>/', views.export_report_excel, name='export_report_excel'),
]
