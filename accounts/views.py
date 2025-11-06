from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import User
from .forms import UserRegistrationForm, UserLoginForm

# Admin-only registration
def register_user(request):
    if 'user_role' not in request.session or request.session['user_role'] != 'admin':
        messages.error(request, "Only admins can register new users.")
        return redirect('login')

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
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    messages.error(request, "This account is inactive.")
                elif check_password(password, user.password):
                    # store session
                    request.session['user_id'] = user.id
                    request.session['user_role'] = user.role

                    # redirect by role
                    if user.role == 'admin':
                        return redirect('admin_dashboard')
                    elif user.role == 'staff':
                        return redirect('staff_dashboard')
                    else:
                        return redirect('normal_dashboard')
                else:
                    messages.error(request, "Invalid password.")
            except User.DoesNotExist:
                messages.error(request, "User does not exist.")
    else:
        form = UserLoginForm()

    # Already logged in? redirect automatically
    if 'user_role' in request.session:
        role = request.session['user_role']
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'staff':
            return redirect('staff_dashboard')
        else:
            return redirect('normal_dashboard')

    return render(request, 'accounts/login.html', {'form': form})

# Logout
def logout_user(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# Dashboards
def admin_dashboard(request):
    if 'user_role' not in request.session or request.session['user_role'] != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    return render(request, 'accounts/admin_dashboard.html')

def staff_dashboard(request):
    if 'user_role' not in request.session or request.session['user_role'] != 'staff':
        messages.error(request, "Access denied.")
        return redirect('login')
    return render(request, 'accounts/staff_dashboard.html')

def normal_dashboard(request):
    if 'user_role' not in request.session or request.session['user_role'] != 'normal':
        messages.error(request, "Access denied.")
        return redirect('login')
    return render(request, 'accounts/normal_dashboard.html')
