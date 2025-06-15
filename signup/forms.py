# signup/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser # <-- Make sure this line is correct!

class StudentSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True) # Ensure email is included if you want it on the form

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'full_name', 'phone_number', 'course', 'gender',)
        # ^^^ Include all CustomUser fields you want collected during student signup

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student' # Set the role for new student
        if commit:
            user.save()
        return user

class LandlordSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True) # Ensure email is included

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'full_name', 'phone_number',)
        # ^^^ Include all CustomUser fields you want collected during landlord signup

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'owner' # Set the role for new landlord (as 'owner' in your login_view)
        if commit:
            user.save()
        return user