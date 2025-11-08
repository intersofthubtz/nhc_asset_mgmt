from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Main Manage Assets page
    path('staff/manage-assets/', views.staff_manage_assets, name='staff_manage_assets'),

    # Add/Edit/Delete/Detail
    path('staff/assets/add/', views.add_asset, name='add_asset'),
    path('staff/assets/<int:pk>/edit/', views.edit_asset, name='edit_asset'),
    path('staff/assets/<int:pk>/delete/', views.delete_asset, name='delete_asset'),
    path('staff/assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    
]
