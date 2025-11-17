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

    # Recent requests
    recent_requests = AssetRequest.objects.filter(status='pending').order_by('-request_date')[:10]

    context = {
        'total_assets': total_assets,
        'pending_requests': pending_requests,
        'approved_assets': approved_assets,
        'returned_assets': returned_assets,
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

# @login_required
# @roles_required('normal')
# @nocache
# def normal_dashboard(request):
#     return render(request, 'accounts/normal_dashboard.html')


@login_required
@roles_required('normal')
@nocache
def normal_dashboard(request):
    user = request.user

    total_assets = Asset.objects.filter(status='available').count()
    user_requests = AssetRequest.objects.filter(user=user)
    pending_requests_count = user_requests.filter(status='pending').count()
    approved_requests_count = user_requests.filter(status='approved').count()
    rejected_requests_count = user_requests.filter(status='rejected').count()

    processed_requests_count = approved_requests_count + rejected_requests_count

    context = {
        'total_assets': total_assets,
        'pending_requests_count': pending_requests_count,
        'approved_requests_count': approved_requests_count,
        'rejected_requests_count': rejected_requests_count,
        'processed_requests_count': processed_requests_count,
    }
    return render(request, 'accounts/normal_dashboard.html', context)

