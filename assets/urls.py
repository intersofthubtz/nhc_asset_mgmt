from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [

    # ============================
    #        ADMIN ROUTES
    # ============================
    path('admin/generate-assets/', views.generate_sample_assets, name='generate_assets'),

    
    path(
        'admin/manage-assets/',
        views.admin_manage_assets,
        name='admin_manage_assets'
    ),
    path(
        'admin/assets/add/',
        views.admin_add_asset,
        name='admin_add_asset'
    ),
    path(
        'admin/assets/<int:pk>/',
        views.admin_asset_detail,
        name='admin_asset_detail'
    ),
    path(
        'admin/assets/<int:pk>/edit/',
        views.admin_edit_asset,
        name='admin_edit_asset'
    ),
    path(
        'admin/assets/<int:pk>/delete/',
        views.admin_delete_asset,
        name='admin_delete_asset'
    ),

    # Admin-only report exporter
    path(
        'admin/export-report/<str:report_type>/',
        views.export_report_excel,
        name='admin_export_report'
    ),


    # ============================
    #        STAFF ROUTES
    # ============================
    path(
        'manage-assets/',
        views.staff_manage_assets,
        name='staff_manage_assets'
    ),
    path(
        'assets/add/',
        views.add_asset,
        name='add_asset'
    ),
    path(
        'assets/<int:pk>/edit/',
        views.edit_asset,
        name='edit_asset'
    ),
    path(
        'assets/<int:pk>/',
        views.asset_detail,
        name='asset_detail'
    ),

    # Staff-only report exporter
    path(
        'export-report/<str:report_type>/',
        views.export_report_excel,
        name='staff_export_report'
    ),
]
