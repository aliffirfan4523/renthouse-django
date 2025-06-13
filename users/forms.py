# users/forms.py

from datetime import date, timedelta
from django import forms
from .models import AdditionalOccupant, Booking, ChatMessage, CustomUser, MaintenanceRequest, Property
from django.forms.widgets import DateInput
from django.core.exceptions import ValidationError # Import ValidationError for custom errors

# Booking Form (MODIFIED: fields moved to Meta class)
# --- Booking Form (MODIFIED: Removed redundant fields, will be handled by occupant_details) ---
class BookingForm(forms.ModelForm):
    # Retrieve choices from CustomUser model
    GENDER_CHOICES = CustomUser.GENDER_CHOICES

    full_name_on_form = forms.CharField(
        label="Full Name",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
        help_text="Full name of the primary booker."
    )
    gender_on_form = forms.ChoiceField(
        label="Gender",
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Gender of the primary booker."
    )
    student_id_number = forms.CharField(
        label="Student ID / Matric No.",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional: Enter your student ID'}),
        help_text="Your student ID or matriculation number."
    )
    email_on_form = forms.EmailField(
        label="Email",
        max_length=100,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
        help_text="Your contact email address."
    )
    current_address_on_form = forms.CharField(
        label="Current Address",
        widget=forms.Textarea(attrs={'placeholder': 'Enter your current address', 'rows': 3}),
        help_text="Your current residential address."
    )
    university_name_on_form = forms.CharField(
        label="University/College Name",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional: Your university/college'}),
        help_text="The name of your university or college."
    )
    expected_duration_of_stay = forms.CharField(
        label="Expected Duration of Stay",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 6 months, 1 year'}),
        help_text="How long do you plan to stay?"
    )
    start_date = forms.DateField(
        label="Check-in Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="The desired check-in date."
    )


    class Meta:
        model = Booking
        fields = [
            'full_name_on_form', 'gender_on_form', 'student_id_number',
            'email_on_form', 'current_address_on_form', 'university_name_on_form',
            'expected_duration_of_stay', 'start_date',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
            'number_of_occupants': forms.NumberInput(attrs={'placeholder': 'Total people staying (including yourself)', 'min': 1}),
            'full_name_on_form': forms.TextInput(attrs={'placeholder': 'Your Full Name'}),
            'gender_on_form': forms.Select(attrs={'class': 'form-select'}),
            'student_id_number': forms.TextInput(attrs={'placeholder': 'Your Student ID / Matriculation Number (Optional)'}),
            'email_on_form': forms.EmailInput(attrs={'placeholder': 'Your Email Address'}),
            'current_address_on_form': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your Current Address'}),
            'university_name_on_form': forms.TextInput(attrs={'placeholder': 'Your University / College Name (Optional)'}),
            'expected_duration_of_stay': forms.TextInput(attrs={'placeholder': 'e.g., 6 Months, 1 Year'}),
        }
        labels = {
            'start_date': 'Expected Move-in Date',
            'number_of_occupants': 'Total Occupants',
            'full_name_on_form': 'Your Full Name',
            'gender_on_form': 'Your Gender',
            'student_id_number': 'Your Student ID / Matriculation Number',
            'email_on_form': 'Your Email Address',
            'current_address_on_form': 'Your Current Address',
            'university_name_on_form': 'Your University / College Name',
            'expected_duration_of_stay': 'Expected Duration of Stay',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        number_of_occupants = cleaned_data.get('number_of_occupants')

        if start_date:
            if start_date < date.today():
                self.add_error('start_date', "Move-in date cannot be in the past.")

        if number_of_occupants is not None and number_of_occupants < 1:
            self.add_error('number_of_occupants', "Total occupants must be at least 1.")

        return cleaned_data


# --- NEW: Form for an individual additional occupant's details ---
class AdditionalOccupantForm(forms.ModelForm):
    # GENDER_CHOICES are now directly on the ModelForm from AdditionalOccupant model
    # which inherits from CustomUser.GENDER_CHOICES via its model field definition.
    
    class Meta:
        model = AdditionalOccupant # <--- IMPORTANT: Link to the new AdditionalOccupant model
        fields = ['full_name', 'student_id_number', 'email', 'phone_number', 'gender']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name of Occupant'}),
            'student_id_number': forms.TextInput(attrs={'placeholder': 'Student ID (Optional)'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = { # Custom labels for clarity in the form
            'full_name': "Full Name:",
            'student_id_number': "Student ID / Matric:",
            'email': "Email:",
            'phone_number': "Phone Number:",
            'gender': "Gender:",
        }

# Create a formset for additional occupants
AdditionalOccupantFormSet = forms.modelformset_factory(
    AdditionalOccupant, # <--- IMPORTANT: Base the formset on the AdditionalOccupant model
    form=AdditionalOccupantForm, # Use the defined ModelForm
    extra=0, # Start with 0 extra forms
    can_delete=True, # Allow deletion of forms
)





class MessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 1, # Start with 1 row, auto-resize with JS
                'placeholder': 'Type your message here...',
                'class': 'chat-message-input' # Used by JS for auto-resize
            }),
        }
        labels = {
            'message': '' # No label for the chat input field
        }


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['issue_title', 'issue_description', 'priority']
        widgets = {
            'issue_title': forms.TextInput(attrs={'placeholder': 'E.g., Leaky Faucet, Broken AC'}),
            'issue_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue in detail...'}),
        }
        labels = {
            'issue_title': 'Issue Title',
            'issue_description': 'Description',
            'priority': 'Priority Level',
        }