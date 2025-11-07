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
    path('staff/manage-requests/', views.manage_requests, name='manage_requests'),
    path('staff/request/<int:pk>/<str:action>/', views.update_request_status, name='update_request_status'),

]
