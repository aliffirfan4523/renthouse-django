# tenant/forms.py

from django import forms
from users.models import MaintenanceRequest # Import from users app

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        # We don't include 'submitted_by' or 'property' here as they'll be set in the view
        fields = ['issue_title', 'issue_description', 'priority',]
        widgets = {
            'issue_title': forms.TextInput(attrs={'placeholder': 'e.g., Leaky faucet, Broken window'}),
            'issue_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue in detail...'}),
            'priority': forms.Select(choices=MaintenanceRequest.PRIORITY_CHOICES),
             'status': forms.Select(choices=MaintenanceRequest.STATUS_CHOICES) # Add a class for styling
        }
        labels = {
            'issue_title': 'What is the issue?',
            'issue_description': 'Tell us more about it:',
            'priority': 'How urgent is this?',
            'status': 'What is the current status?',
        }