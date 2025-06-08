# landlord/urls.py

from django.urls import path
from . import views

app_name = 'owner' # NEW: Namespace for the landlord app

urlpatterns = [
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    # Add URLs for booking actions (confirm/reject) and maintenance actions later
]