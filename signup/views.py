# C:\Users\T U F\Documents\GitHub\renthouse-django\signup\views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from signup.forms import LandlordSignUpForm, StudentSignUpForm

def student_signup_view(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            print("DEBUG: Form is VALID for Student!") # This will print to your terminal
            try:
                user = form.save()
                print(f"DEBUG: Student User '{user.username}' (role: {user.role}) saved successfully to DB.") # This will print to your terminal
                messages.success(request, 'Student account created successfully! Please log in.')
                return redirect('login:login')
            except Exception as e:
                print(f"DEBUG: Error saving student user: {e}") # If save fails for unexpected reason
                messages.error(request, f'An unexpected error occurred: {e}')
        else:
            print("DEBUG: Form is NOT VALID for Student.") # This will print to your terminal
            print("DEBUG: Student Form Errors:", form.errors.as_data()) # This will show detailed errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentSignUpForm()
    return render(request, 'student_signup.html', {'form': form})

def landlord_signup_view(request):
    if request.method == 'POST':
        form = LandlordSignUpForm(request.POST)
        if form.is_valid():
            print("DEBUG: Form is VALID for Landlord!") # This will print to your terminal
            try:
                user = form.save()
                print(f"DEBUG: Landlord User '{user.username}' (role: {user.role}) saved successfully to DB.") # This will print to your terminal
                messages.success(request, 'Owner account created successfully! Please log in.')
                return redirect('login:login')
            except Exception as e:
                    print(f"DEBUG: Error saving landlord user: {e}") # If save fails for unexpected reason
                    messages.error(request, f'An unexpected error occurred: {e}')
        else:
            print("DEBUG: Form is NOT VALID for Landlord.") # This will print to your terminal
            print("DEBUG: Landlord Form Errors:", form.errors.as_data()) # This will show detailed errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LandlordSignUpForm()
    return render(request, 'landlord_signup.html', {'form': form})