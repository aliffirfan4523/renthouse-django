# owner/urls.py

from django.urls import path
from . import views

app_name = 'owner' # NEW: Namespace for the Owner app

urlpatterns = [
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('dashboard/<int:pk>/', views.PropertyPreView.as_view(), name='property_detail'),
    path('add-property', views.add_property, name='add_property'), # Link to the new view
    path('bookings/<int:booking_pk>/details/', views.view_booking_details, name='view_booking_details'),
    path('bookings/<int:booking_pk>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('bookings/<int:booking_pk>/reject/', views.reject_booking, name='reject_booking'),
    # Add URLs for booking actions (confirm/reject) and maintenance actions later
]