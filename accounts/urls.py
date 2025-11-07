from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Admin-only registration
    path('register/', views.register_user, name='register'),

    # Dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/manage-assets/', views.staff_manage_assets, name='staff_manage_assets'),
    path('staff/manage-requests/', views.staff_manage_requests, name='staff_manage_requests'),
    path('staff/report/', views.staff_report, name='staff_report'),
    path('normal/dashboard/', views.normal_dashboard, name='normal_dashboard'),
]
