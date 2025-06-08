
from datetime import timezone
from django.template import loader
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Booking, CustomUser, MaintenanceRequest, Property, ChatMessage # Import models from users app
from .forms import MaintenanceRequestForm # Import the new form
from django.db.models import Q # For querying latest chat messages

@login_required
# Create your views here.
def tenant_home(request):
    return render (request,"tenant/index.html")

@login_required
def tenant_dashboard(request):
    # Ensure only tenant (and potentially admins for testing) can access this
    if not (request.user.role == 'tenant' or request.user.is_superuser):
        messages.error(request, "Access Denied. You must be a tenant to view this dashboard.")
        return redirect('users:home') # Redirect to general home page

    # --- Data for 'My Current Rental(s)' ---
    # Assuming a tenant can only have one active confirmed booking for a property at a time
    current_rental = Booking.objects.filter(
        tenant=request.user,
        status='confirmed',
        end_date__gte=timezone.now().date() # Ensure end date is in future/today
    ).select_related('property', 'property__owner').order_by('-start_date').first()

    # --- Data for 'My Bookings' ---
    all_bookings = Booking.objects.filter(tenant=request.user).order_by('-booking_date')

    # --- Data for 'Maintenance Requests' ---
    if request.method == 'POST':
        # Check if the POST is for submitting a maintenance request
        if 'submit_maintenance' in request.POST:
            # We need to know which property the request is for.
            # Assuming it's for their current rental if they have one.
            # If not, you might need a dropdown in the form to select a property.
            if current_rental:
                maintenance_form = MaintenanceRequestForm(request.POST)
                if maintenance_form.is_valid():
                    maintenance_request = maintenance_form.save(commit=False)
                    maintenance_request.submitted_by = request.user
                    maintenance_request.property = current_rental.property # Link to their current rental property
                    maintenance_request.save()
                    messages.success(request, "Your maintenance request has been submitted!")
                    return redirect('tenant:tenant_dashboard') # Redirect to clear form
                else:
                    messages.error(request, "Please correct the errors in the maintenance request form.")
            else:
                messages.error(request, "You must have a current rental to submit a maintenance request.")
        # Add other POST handling for other forms if necessary
    else:
        maintenance_form = MaintenanceRequestForm()

    my_maintenance_requests = MaintenanceRequest.objects.filter(submitted_by=request.user).order_by('-submitted_date')

    # --- Data for 'Recent Chats' ---
    # --- Data for 'Recent Chats' ---
    recent_chats_data = []
    # Identify all properties and other users this user has chatted with
    involved_properties = ChatMessage.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).values_list('property', flat=True).distinct()

    for prop_id in involved_properties:
        # Find the other participant(s) in chats related to this property
        # FIX: Place the Q object before the keyword argument (property_id)
        other_participants = ChatMessage.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user), # Q object first (positional)
            property=prop_id # Then keyword argument (use 'property' object or 'property_id' directly)
        ).exclude(
            Q(sender=request.user, receiver=request.user)
        ).values_list('sender', 'receiver').distinct()

        for s, r in other_participants:
            other_user_id = s if s != request.user.pk else r
            # Make sure 'other_user' is not the current user's ID
            if other_user_id == request.user.pk:
                continue # Skip if somehow we end up with the current user as the "other"

            other_user = CustomUser.objects.get(pk=other_user_id)

            # Get the last message in this specific conversation (property + other user)
            # FIX: Place the Q object first here as well
            last_message = ChatMessage.objects.filter(
                Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user), # Q object first
                property=prop_id # Then keyword argument
            ).order_by('-timestamp').first()

            if last_message:
                recent_chats_data.append({
                    'property': Property.objects.get(pk=prop_id), # Get the property object
                    'other_user': other_user,
                    'last_message_text': last_message.message,
                    'last_message_timestamp': last_message.timestamp,
                    'link': reverse('users:chat_with_owner', args=[prop_id, other_user_id])
                })
    # Sort these recent chats by the timestamp of their last message
    recent_chats_data.sort(key=lambda x: x['last_message_timestamp'], reverse=True)



    context = {
        'current_rental': current_rental,
        'all_bookings': all_bookings,
        'maintenance_form': maintenance_form,
        'my_maintenance_requests': my_maintenance_requests,
        'recent_chats_data': recent_chats_data,
        'logo_text_color': '#7fc29b', # For header consistency
        'header_button_color': '#e91e63', # For header consistency
    }
    return render(request, 'tenant/index.html', context)
