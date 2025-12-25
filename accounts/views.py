import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
import openpyxl
from openpyxl.styles import Font, PatternFill

from assets.forms import AssetForm
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
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, "Access denied.")
                return redirect('accounts:permission_denied')  # optional page
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
        redirect_map = {
            'admin': 'accounts:admin_dashboard',
            'staff': 'accounts:staff_dashboard',
            'normal': 'accounts:normal_dashboard'
        }
        return redirect(redirect_map.get(request.user.role, 'accounts:login'))

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            redirect_map = {
                'admin': 'accounts:admin_dashboard',
                'staff': 'accounts:staff_dashboard',
                'normal': 'accounts:normal_dashboard'
            }
            return redirect(redirect_map.get(user.role, 'accounts:login'))
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('accounts:login')

# --- User Registration (Admin Only) ---

@login_required
@roles_required('admin')
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User registered successfully.")
            return redirect('accounts:admin_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

# --- Dashboards ---

@login_required
@roles_required('admin')
@nocache
def admin_dashboard(request):
    total_assets = Asset.objects.count()
    pending_requests = AssetRequest.objects.filter(status='pending').count()
    approved_assets = Asset.objects.filter(status='borrowed').count()
    returned_assets = Asset.objects.filter(status='returned').count()
    recent_requests = AssetRequest.objects.filter(status='pending').order_by('-request_date')[:10]

    context = {
        'total_assets': total_assets,
        'pending_requests': pending_requests,
        'approved_assets': approved_assets,
        'returned_assets': returned_assets,
        'recent_requests': recent_requests,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@roles_required('admin')
def admin_report(request):
    context = {
        # Add report context here
    }
    return render(request, 'assets/admin_report.html', context)

@login_required
@roles_required('staff')
def staff_dashboard(request):
    total_assets = Asset.objects.count()
    pending_requests = AssetRequest.objects.filter(status='pending').count()
    approved_assets = Asset.objects.filter(status='borrowed').count()
    returned_assets = Asset.objects.filter(status='returned').count()
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
    context = {
        # Add staff report context
    }
    return render(request, 'assets/staff_report.html', context)

# --- Normal User Dashboard ---
@login_required
@roles_required('normal')
@nocache
def normal_dashboard(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "all")
    category_filter = request.GET.get("category", "all")

    qs = AssetRequest.objects.filter(user=request.user)

    # SEARCH
    if search_query:
        qs = qs.filter(
            Q(asset_category__icontains=search_query) |
            Q(remarks__icontains=search_query)
        )

    # STATUS FILTER
    if status_filter != "all":
        qs = qs.filter(status=status_filter)

    # CATEGORY FILTER
    if category_filter != "all":
        qs = qs.filter(asset_category=category_filter)

    qs = qs.order_by("-request_date")

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "category_filter": category_filter,

        # stats
        "pending_requests_count": qs.filter(status="pending").count(),
        "approved_requests_count": qs.filter(status="approved").count(),
        "rejected_requests_count": qs.filter(status="rejected").count(),
    }

    return render(request, "accounts/normal_dashboard.html", context)

