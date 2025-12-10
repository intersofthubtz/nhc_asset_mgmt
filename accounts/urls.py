from django.urls import path
from . import views

app_name = 'accounts'  # <- add this line

urlpatterns = [
    # Authentication
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Admin-only registration
    path('register/', views.register_user, name='register'),

    # Dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/report/', views.admin_report, name='admin_report'),
    
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/report/', views.staff_report, name='staff_report'),

    # Normal user dashboard
    path('dashboard/', views.normal_dashboard, name='normal_dashboard'),
]
