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


def login_view(request):
    if request.user.is_authenticated:
        # If user is already logged in, redirect them based on their actual role
        if request.user.role == 'owner':
            return redirect('owner:owner_dashboard')
        elif request.user.role == 'student':
            return redirect('users:home')
        elif request.user.role == 'admin': # Consider a separate admin dashboard
            return redirect('admin:index')
        return redirect('users:home') # Default for any other role or general redirect

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Get the role type selected on the form (client-side input)
        role_type_from_form = request.POST.get('role_type')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # --- NEW VALIDATION LOGIC START ---
            # Compare the role selected on the form with the user's actual role from the database
            if user.role != role_type_from_form and user.role != 'admin':
                messages.error(request, f"Account Not Found")
                # Re-render the login page, keeping the selected role_type from the form
                # so the toggle button state reflects the user's choice.
                return render(request, 'login/login.html', {'role_type_initial': role_type_from_form})
            # --- NEW VALIDATION LOGIC END ---

            # If roles match, proceed with login
            login(request, user)
            #messages.success(request, f"Welcome back, {user.full_name or user.username}!")

            # Redirect based on the user's actual, verified role
            if user.role == 'owner':
                return redirect('owner:owner_dashboard')
            elif user.role == 'student':
                return redirect('users:home')
            elif user.role == 'admin':
                return redirect('admin:index')
            else:
                return redirect('users:home') # Fallback

        else:
            # Authentication (username/password) failed
            messages.error(request, "Invalid username or password. Please try again.")
            # Re-render the login page with error, preserving the selected role_type from the form
            return render(request, 'login/login.html', {'role_type_initial': role_type_from_form})

    # For GET request, render the empty login form
    # You might want to pass an initial role_type if you want a default state for the toggle
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