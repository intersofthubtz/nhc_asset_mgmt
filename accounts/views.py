from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps

from assets.models import Asset
from requests.models import AssetRequest
from .forms import UserRegistrationForm, UserLoginForm

# --- Decorators ---

def roles_required(*roles):
    """Allow only users with specified roles to access view"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role not in roles:
                messages.error(request, "Access denied.")
                return redirect('login')
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
        # Already logged in → redirect by role
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'staff':
            return redirect('staff_dashboard')
        else:
            return redirect('normal_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            # Redirect by role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'staff':
                return redirect('staff_dashboard')
            else:
                return redirect('normal_dashboard')
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

# --- Admin Registration ---

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

@login_required
@roles_required('staff')
@nocache
def staff_dashboard(request):
    return render(request, 'accounts/staff_dashboard.html')

@login_required
@roles_required('staff')
@nocache
def staff_dashboard(request):
    return render(request, 'accounts/staff_dashboard.html')

@login_required
@roles_required('staff')
@nocache
def staff_manage_assets(request):
    # Fetch assets if needed
    return render(request, 'assets/staff_manage_assets.html')

@login_required
@roles_required('staff')
@nocache
def staff_manage_requests(request):
    # Fetch requests if needed
    return render(request, 'requests/staff_manage_requests.html')

@login_required
@roles_required('staff')
@nocache
def staff_report(request):
    # Generate reports if needed
    return render(request, 'assets/staff_report.html')



@login_required
@roles_required('normal')
@nocache
@login_required
def normal_dashboard(request):
    # Total available assets
    total_available_assets = Asset.objects.filter(status='available').count()

    # Count of user's requests by status
    pending_requests_count = AssetRequest.objects.filter(user=request.user, status='pending').count()
    approved_requests_count = AssetRequest.objects.filter(user=request.user, status='returned').count()
    rejected_requests_count = AssetRequest.objects.filter(user=request.user, status='rejected').count()

    # Total processed requests (only approved + rejected)
    processed_requests_count = approved_requests_count + rejected_requests_count

    context = {
        'total_assets': total_available_assets,
        'pending_requests_count': pending_requests_count,
        'processed_requests_count': processed_requests_count,
        'approved_requests_count': approved_requests_count,
        'rejected_requests_count': rejected_requests_count,
    }

    return render(request, 'accounts/normal_dashboard.html', context)
