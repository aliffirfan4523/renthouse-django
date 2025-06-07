# users/forms.py

from datetime import timedelta
from django import forms
from .models import Booking, CustomUser, Property
from django.forms.widgets import DateInput
from django.core.exceptions import ValidationError # Import ValidationError for custom errors

class BookingForm(forms.ModelForm):
    full_name_on_form = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name'})
    )
    student_id_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Student ID / Matriculation Number'})
    )
    email_on_form = forms.EmailField(
        max_length=100,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    current_address_on_form = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Current Address'}),
        required=False
    )
    university_name_on_form = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'University / College Name'})
    )

    start_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date'}),
        help_text='Expected Move-in Date'
    )
    end_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date'}),
        help_text='Expected Move-out Date'
    )
    expected_duration_of_stay = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 6 months, 1 year'})
    )
    spots_booked = forms.IntegerField(
        min_value=1,
        # Max value will be set in __init__ based on property.available_spots
        widget=forms.NumberInput(attrs={'placeholder': 'Number of spots/rooms'})
    )

    class Meta:
        model = Booking
        fields = [
            'full_name_on_form', 'student_id_number', 'email_on_form',
            'current_address_on_form', 'university_name_on_form',
            'start_date', 'end_date', 'expected_duration_of_stay', 'spots_booked'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.property_obj = kwargs.pop('property_obj', None)
        super().__init__(*args, **kwargs)

        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            self.fields['full_name_on_form'].initial = user.full_name
            self.fields['email_on_form'].initial = user.email
            # Assuming CustomUser has these fields, pre-fill them:
            if hasattr(user, 'phone_number'):
                 # Assuming phone_number can also serve as a current address placeholder for now
                 self.fields['current_address_on_form'].initial = user.phone_number
            if hasattr(user, 'course'):
                 self.fields['university_name_on_form'].initial = user.course
            if hasattr(user, 'student_id_number'):
                 self.fields['student_id_number'].initial = user.student_id_number


        # Set max_value for spots_booked based on property's available_spots
        if self.property_obj:
            self.fields['spots_booked'].widget.attrs['max'] = self.property_obj.available_spots
            self.fields['spots_booked'].help_text = f"Only {self.property_obj.available_spots} spots available."


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        spots_booked = cleaned_data.get('spots_booked')

        if start_date and end_date:
            if start_date and end_date:
                if start_date >= end_date:
                    self.add_error('end_date', "End date must be after start date.") # Add error to specific field
                elif end_date < start_date + timedelta(days=180):
                    self.add_error('end_date', "End date must be at least 6 months after start date.")
        if self.property_obj and spots_booked is not None:
            if spots_booked <= 0:
                 self.add_error('spots_booked', "Number of spots must be at least 1.")
            elif spots_booked > self.property_obj.available_spots:
                self.add_error('spots_booked', f"Cannot book {spots_booked} spots. Only {self.property_obj.available_spots} spots available for {self.property_obj.title}.")

        return cleaned_data
    
# --- NEW: MessageForm for chat messages ---
class MessageForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Type your message here...',
            'class': 'chat-message-input' # Add a class for styling
        }),
        label='' # No label needed for this field
    )