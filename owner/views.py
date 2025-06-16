import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from django.contrib import messages
import pdfkit
from users.models import PaymentRecord, Property, Booking, MaintenanceRequest, ChatMessage, CustomUser, PropertyForm # Import all necessary models
from django.db.models import Q # Q object for complex queries
from django.urls import reverse # To dynamically get URL patterns
from django.utils import timezone
from datetime import date,datetime # For current date comparisons
from django.template.loader import render_to_string # Import render_to_string

@login_required
def owner_dashboard(request):
    """
    Displays the owner dashboard with owned properties, pending bookings,
    maintenance requests, and recent chats.
    Accessible only by users with the 'owner' role or a superuser.
    """
    # Authorization check: Only owners (or superusers) can access this dashboard
    if not (request.user.role == 'owner' or request.user.is_superuser):
        messages.error(request, "Access Denied. You must be a owner to view this dashboard.")
        return redirect('users:home') # Redirect to general home page

    # --- My Properties ---
    # Retrieve all properties owned by the current owner
    owner_properties = Property.objects.filter(owner=request.user).order_by('-created_at')

    # --- Booking Management ---
    # Retrieve all pending booking requests for THIS owner's properties
    pending_bookings = Booking.objects.filter(
        property__owner=request.user, # Filter bookings related to current owner's properties
        status='pending' # Only show pending bookings
    ).order_by('start_date') # Order by oldest booking date first

    # Retrieve ALL bookings (pending, confirmed, rejected, cancelled, completed) for this owner's properties
    all_owner_bookings = Booking.objects.filter(
        property__owner=request.user
    ).order_by('-start_date') # Order by most recent booking date first


    # --- Maintenance Requests ---
    # Retrieve all maintenance requests submitted for THIS owner's properties
    owner_maintenance_requests = MaintenanceRequest.objects.filter(
        property__owner=request.user # Filter requests related to current owner's properties
    ).order_by('-submitted_date') # Order by most recent submission

     # --- Received Payments (NEW) ---
    my_received_payments = PaymentRecord.objects.filter(
        receiver_of_payment=request.user
    ).order_by('-payment_date').select_related('user', 'booking') # Select related user and booking
    
    # --- Recent Chats ---
    # Similar logic as in users.views.recent_chats_api_view to get unique conversations
    recent_chats_data = []
    # Get all messages where the current owner is either sender or receiver, ordered by timestamp descending
    all_owner_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp').select_related('property', 'sender', 'receiver') # Optimize with select_related

    processed_conversations = set() # To prevent showing the same conversation multiple times

    for msg in all_owner_messages:
        # Determine the 'other' participant in the conversation
        other_participant = msg.sender if msg.receiver == request.user else msg.receiver

        # Skip if the 'other user' is the current user themselves (self-chat)
        if other_participant == request.user:
            continue

        # Create a canonical key for the conversation pair (property_id, other_user_id)
        # Handle cases where property might be None if a general chat was initiated without a property context
        conversation_key = (msg.property.pk if msg.property else None, other_participant.pk)

        if conversation_key in processed_conversations:
            continue # If this conversation is already processed, skip

        processed_conversations.add(conversation_key) # Mark this conversation as processed

        # Append chat details to the list
        recent_chats_data.append({
            'property': msg.property, # Related Property object
            'other_user': other_participant, # The other CustomUser object
            'last_message_text': msg.message, # Last message content
            'last_message_timestamp': msg.timestamp, # Timestamp of the last message
            # Generate the URL for the chat page dynamically
            'link': reverse('users:chat_with_user', args=[msg.property.pk if msg.property else 0, other_participant.pk])
        })

    # Prepare context dictionary to pass data to the template
    context = {
        'owner_properties': owner_properties,
        'pending_bookings': pending_bookings,
        'all_owner_bookings': all_owner_bookings,
        'owner_maintenance_requests': owner_maintenance_requests,
        'my_received_payments': my_received_payments, # Add received payments to context
        'recent_chats_data': recent_chats_data,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
        'current_date': date.today(), # Useful for date comparisons in templates
    }
    return render(request, 'owner_dashboard.html', context)

class PropertyPreView(DetailView):
    """
    A view to display the detailed information of a single property.
    """
    model = Property
    template_name = 'property_preview.html'
    context_object_name = 'property' # The variable name to use in the template

    def get_context_data(self, **kwargs):
        """
        Adds additional context variables to the template.
        """
        context = super().get_context_data(**kwargs)
        context['logo_text_color'] = '#7fc29b'
        context['header_button_color'] = '#e91e63'
        return context
    

@login_required # Ensures only logged-in users can access
def add_property(request):
    # Only allow owner to add properties
    if not request.user.is_authenticated or request.user.role != 'owner':
        messages.error(request, "Access Denied. Only owner can add properties.")
        return redirect('users:home') # Redirect to home or a forbidden page

    if request.method == 'POST':
        # Pass request.FILES for image uploads
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_instance = form.save(commit=False) # Create property object but don't save yet
            property_instance.owner = request.user # Set the owner to the logged-in user
            property_instance.is_available = True # New properties are available by default
            property_instance.save() # Save the property to the database

            # Save ManyToMany relationships (e.g., amenities)
            # This must be done after the instance is saved to the database
            form.save_m2m() # Saves the amenities (Many-to-Many field)

            messages.success(request, 'Your property has been successfully added!')
            return redirect('users:property_detail', pk=property_instance.pk) # Redirect to the new property's detail page
        else:
            messages.error(request, 'Please correct the errors below.')
            # Errors will be displayed automatically by the form in the template
    else:
        form = PropertyForm() # Create an empty form for GET request

    context = {
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'add_property.html', context)

@login_required
def view_booking_details(request, booking_pk):
    """
    Displays the details of a specific booking for the owner,
    including options to confirm or reject.
    """
    booking = get_object_or_404(Booking.objects.select_related('property', 'tenant'), pk=booking_pk)

    # Authorization check: Only the property owner or superuser can view these details
    if request.user != booking.property.owner and not request.user.is_superuser:
        messages.error(request, "Access Denied. You are not authorized to view these booking details.")
        return redirect('owner:owner_dashboard')

    # MODIFIED: Get AdditionalOccupant objects directly through the related_name
    # The related_name is 'additional_occupants' on the Booking model.
    # So, `booking.additional_occupants.all()` will return a queryset of AdditionalOccupant objects.
    additional_occupants = booking.additional_occupants.all().order_by('full_name')


    context = {
        'booking': booking,
        'property': booking.property, # Access the related property
        'additional_occupants': additional_occupants, # Pass the queryset of AdditionalOccupant objects
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'view_booking_details.html', context)


@login_required
def confirm_booking(request, booking_pk):
    """
    Allows a owner to confirm a pending booking.
    """
    booking = get_object_or_404(Booking, pk=booking_pk)

    # Authorization check: Only the property owner or superuser can confirm
    if request.user != booking.property.owner and not request.user.is_superuser:
        messages.error(request, "Access Denied. You are not authorized to perform this action.")
        return redirect('owner:owner_dashboard')

    if request.method == 'POST':
        if booking.status == 'pending':
            booking.status = 'confirmed'
            booking.save()
            # Optionally, mark the property as unavailable if it's a whole-house booking
            # and the property logic requires it upon confirmation.
            # property_obj.is_available = False # Re-evaluate this based on your `is_available` logic
            # property_obj.save()
            messages.success(request, f"Booking for {booking.property.title} confirmed successfully!")
        else:
            messages.error(request, f"Booking is not in 'pending' status and cannot be confirmed.")
    else:
        messages.warning(request, "Invalid request method.") # Should only be accessed via POST

    return redirect('owner:owner_dashboard') # Redirect back to owner dashboard


@login_required
def reject_booking(request, booking_pk):
    """
    Allows a owner to reject a pending booking.
    """
    booking = get_object_or_404(Booking, pk=booking_pk)

    # Authorization check: Only the property owner or superuser can reject
    if request.user != booking.property.owner and not request.user.is_superuser:
        messages.error(request, "Access Denied. You are not authorized to perform this action.")
        return redirect('owner:owner_dashboard')

    if request.method == 'POST':
        if booking.status == 'pending':
            booking.status = 'rejected'
            booking.save()
            # If rejected, you might want to make the property available again if it was temporarily held
            # property_obj.is_available = True # Re-evaluate this based on your `is_available` logic
            # property_obj.save()
            messages.success(request, f"Booking for {booking.property.title} rejected.")
        else:
            messages.error(request, f"Booking is not in 'pending' status and cannot be rejected.")
    else:
        messages.warning(request, "Invalid request method.") # Should only be accessed via POST

    return redirect('owner:owner_dashboard') # Redirect back to owner dashboard

def update_status(request, id):
    # Fetch the maintenance request by ID
    maintenance_request = get_object_or_404(MaintenanceRequest, id=id)

    # Get the new status from the form
    new_status = request.POST.get('status')

    # If the new status is valid, update the request
    if new_status in dict(MaintenanceRequest.STATUS_CHOICES).keys():
        maintenance_request.status = new_status
        maintenance_request.save()
        messages.success(request, f"Status updated to {new_status.capitalize()}.")
    else:
        messages.error(request, "Invalid status change.")

    # Redirect back to the dashboard
    return redirect('owner:owner_dashboard')

def resolve_note_view(request, req_id):
    # Get the maintenance request
    maintenance_request = get_object_or_404(MaintenanceRequest, id=req_id)

    if request.method == 'POST':
        # Get data from the form submission
        resolution_notes = request.POST.get('resolution_notes')
        status = request.POST.get('status')
        resolved_date = timezone.now()  # Automatically set the resolve date as the current time


        
        # Save the resolve note, status, and resolve date
        maintenance_request.resolution_notes = resolution_notes
        maintenance_request.status = status
        maintenance_request.resolved_date = resolved_date

        # Save the changes to the database
        maintenance_request.save()

        # Redirect back to the owner dashboard after saving
        return redirect('owner:owner_dashboard')  # Adjust the name of the view if necessary

    return JsonResponse({"success": False, "message": "Invalid request."})
@login_required
def edit_property(request, pk):
    """
    Allows a landlord (owner) to edit details of their property.
    Only the property owner or an admin can access this view.
    """
    property_instance = get_object_or_404(Property, pk=pk)

    # Authorization check
    if not (request.user == property_instance.owner or request.user.is_superuser):
        messages.error(request, "Access Denied. You are not authorized to edit this property.")
        return redirect('landlord:landlord_dashboard') # Redirect to landlord dashboard or home

    if request.method == 'POST':
        # Pass request.FILES for image uploads
        form = PropertyForm(request.POST, request.FILES, instance=property_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Property '{property_instance.title}' updated successfully!")
            return redirect('landlord:landlord_dashboard') # Redirect back to landlord dashboard
        else:
            messages.error(request, "Please correct the errors in the form.")
    else: # GET request
        form = PropertyForm(instance=property_instance) # Pre-fill form with existing data

    context = {
        'form': form,
        'property': property_instance,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'edit_property.html', context)

def receipt_view_owner(request, pk):
    """
    Displays the payment receipt by retrieving the PaymentRecord from the database.
    """
    payment_record = get_object_or_404(PaymentRecord, pk=pk)

    context = {
        'payment_record': payment_record,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'receipt.html', context)
