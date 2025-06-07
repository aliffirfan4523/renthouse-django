from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages



# --- NEW: Login View ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:home') # Redirect already logged-in users

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role_type = request.POST.get('role_type') # Get the role type from the hidden field

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user) # Log the user in
            messages.success(request, f"Welcome back, {user.full_name or user.username}!")
            # You can redirect based on role_type if needed here
            # For now, just redirect to home page
            return redirect('users:home')
        else:
            # Authentication failed
            messages.error(request, "Invalid username or password. Please try again.")
            # Re-render the login page with an error message
            # Pass role_type back to keep the UI state on failed login
            return render(request, 'login/login.html', {'role_type_initial': role_type})

    # For GET request, render the empty login form
    return render(request, 'login/login.html')

# --- NEW: Logout View ---
def logout_view(request):
    logout(request)
    return redirect('login:login') # Redirect to login page after logout

def register_user(request):
    return render(request, 'login/register_user.html')  # Basic placeholder

def admin_login(request):
    return render(request, 'login/adminLogin.html')  # Basic placeholder

def admin_logout(request):
    logout(request)
    return redirect('adminLogin')