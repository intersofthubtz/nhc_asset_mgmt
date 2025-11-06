from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from .forms import UserRegistrationForm, UserLoginForm
from .models import User

# Custom decorator for role-based access
def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role != role:
                messages.error(request, "Access denied.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Admin-only registration
@login_required
@role_required('admin')
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


# Login
def login_user(request):
    if request.user.is_authenticated:
        # Already logged in, redirect by role
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

            # redirect by role
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


# Logout
@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# Dashboards
@login_required
@role_required('admin')
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


@login_required
@role_required('staff')
def staff_dashboard(request):
    return render(request, 'accounts/staff_dashboard.html')


@login_required
@role_required('normal')
def normal_dashboard(request):
    return render(request, 'accounts/normal_dashboard.html')
