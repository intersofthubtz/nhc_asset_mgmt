from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from assets.models import Asset
from requests.models import AssetRequest
from .forms import UserRegistrationForm, UserLoginForm
import logging

# --- Decorators ---

def roles_required(*roles):
    """Allow only users with specified roles to access view"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please login first.")
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, "Access denied.")
                return redirect('permission_denied')  # Optional: create a dedicated page
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def nocache(view_func):
    """Prevent browser caching for sensitive pages"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        from django.utils.cache import add_never_cache_headers
        add_never_cache_headers(response)
        return response
    return wrapper

# --- Authentication Views ---

def login_user(request):
    if request.user.is_authenticated:
        # Redirect based on role
        redirect_map = {
            'admin': 'admin_dashboard',
            'staff': 'staff_dashboard',
            'normal': 'normal_dashboard'
        }
        return redirect(redirect_map.get(request.user.role, 'login'))

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            redirect_map = {
                'admin': 'admin_dashboard',
                'staff': 'staff_dashboard',
                'normal': 'normal_dashboard'
            }
            return redirect(redirect_map.get(user.role, 'login'))
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# --- User Registration (Admin Only) ---

@login_required
@roles_required('admin')
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User registered successfully.")
            return redirect('admin_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

# --- Dashboards ---

@login_required
@roles_required('admin')
@nocache
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')



logger = logging.getLogger(__name__)

def staff_dashboard(request):
    # Total assets
    total_assets = Asset.objects.count()

    # Pending requests
    pending_requests = AssetRequest.objects.filter(status='pending').count()

    # Approved assets (borrowed)
    approved_assets_qs = Asset.objects.filter(status='borrowed')
    approved_assets = approved_assets_qs.count()

    # Returned assets
    returned_assets_qs = Asset.objects.filter(status='returned')
    returned_assets = returned_assets_qs.count()

    # Debug output
    print("=== STAFF DASHBOARD DEBUG ===")
    print(f"Total Assets: {total_assets}")
    print(f"Pending Requests: {pending_requests}")
    print(f"Approved Assets (borrowed): {approved_assets}")
    print(f"Returned Assets: {returned_assets}")
    print("Approved Assets List:", list(approved_assets_qs.values('id', 'asset_name', 'status')))
    print("Returned Assets List:", list(returned_assets_qs.values('id', 'asset_name', 'status')))
    print("============================")

    # Recent requests
    recent_requests = AssetRequest.objects.order_by('-request_date')[:5]

    context = {
        'total_assets': total_assets,
        'pending_requests': pending_requests,
        'approved_assets': approved_assets,
        'returned_assets': returned_assets,
        'recent_requests': recent_requests,
    }
    return render(request, 'accounts/staff_dashboard.html', context)



# @login_required
# @roles_required('staff')
# @nocache
# def staff_dashboard(request):
#     # Total assets
#     total_assets = Asset.objects.count()

#     # Pending requests (from AssetRequest)
#     pending_requests = AssetRequest.objects.filter(status='pending').count()

#     # Approved assets (from Asset model)
#     approved_assets = Asset.objects.filter(status='borrowed').count()

#     # Returned assets (from Asset model)
#     returned_assets = Asset.objects.filter(status='returned').count()

#     # Recent requests (latest 5)
#     recent_requests = AssetRequest.objects.order_by('-request_date')[:5]

#     context = {
#         'total_assets': total_assets,
#         'pending_requests': pending_requests,
#         'approved_assets': approved_assets,
#         'returned_assets': returned_assets,
#         'recent_requests': recent_requests,
#     }
#     return render(request, 'accounts/staff_dashboard.html', context)





@login_required
def staff_dashboard(request):
    total_assets = Asset.objects.count()
    pending_requests = AssetRequest.objects.filter(status='pending').count()
    returned_assets = AssetRequest.objects.filter(status='returned').count()
    overdue_returns = AssetRequest.objects.filter(
        status='approved', return_date__lt=timezone.localdate()
    ).count()
    recent_requests = AssetRequest.objects.order_by('-request_date')[:5]

    context = {
        'total_assets': total_assets,
        'pending_requests': pending_requests,
        'returned_assets': returned_assets,
        'overdue_returns': overdue_returns,
        'recent_requests': recent_requests,
    }
    return render(request, 'accounts/staff_dashboard.html', context)
@login_required
@roles_required('staff')
@nocache
def staff_manage_assets(request):
    assets = Asset.objects.all()
    return render(request, 'assets/staff_manage_assets.html', {'assets': assets})

@login_required
@roles_required('staff')
@nocache
def staff_manage_requests(request):
    requests = AssetRequest.objects.select_related('user', 'asset').all()
    return render(request, 'requests/staff_manage_requests.html', {'requests': requests})

@login_required
@roles_required('staff')
@nocache
def staff_report(request):
    # Optional: pass data for reports
    return render(request, 'assets/staff_report.html')

@login_required
@roles_required('normal')
@nocache
def normal_dashboard(request):
    return render(request, 'accounts/normal_dashboard.html')
