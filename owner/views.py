# owner/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Property, Booking, MaintenanceRequest, ChatMessage, CustomUser # Import CustomUser
from django.db.models import Q, Max
from django.urls import reverse
from datetime import date # For current date comparisons

@login_required
def owner_dashboard(request):
    # Ensure only owners (and superusers for testing) can access this
    if not (request.user.role == 'owner' or request.user.is_superuser):
        messages.error(request, "Access Denied. You must be a owner to view this dashboard.")
        return redirect('users:home') # Redirect to general home page

    owner_properties = Property.objects.filter(owner=request.user).order_by('-created_at')

    # --- Booking Management ---
    # Pending Booking Requests for THIS owner's properties
    pending_bookings = Booking.objects.filter(
        property__owner=request.user,
        status='pending'
    ).order_by('booking_date')

    # All Bookings for THIS owner's properties
    all_owner_bookings = Booking.objects.filter(
        property__owner=request.user
    ).order_by('-booking_date')


    # --- Maintenance Requests for THIS owner's properties ---
    owner_maintenance_requests = MaintenanceRequest.objects.filter(
        property__owner=request.user
    ).order_by('-submitted_date')

    # --- REVISED Data for 'Recent Chats' ---
    recent_chats_data = []

    # Get all messages where the current owner is either sender or receiver, ordered by timestamp descending
    all_owner_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    # Use a set to keep track of processed conversation pairs (property_id, other_user_id)
    # This prevents adding duplicate conversations (e.g., if multiple messages exist)
    processed_conversations = set()

    for msg in all_owner_messages:
        # Determine the other participant in this specific message context
        # The other participant is the one who is NOT the current logged-in user
        other_participant_id = msg.sender.pk if msg.receiver == request.user else msg.receiver.pk

        # If the other participant is the owner themselves (self-chat), skip
        if other_participant_id == request.user.pk:
            continue

        # Create a unique key for this conversation (property, other user)
        conversation_key = (msg.property.pk, other_participant_id)

        # If we've already processed the latest message for this conversation, skip
        if conversation_key in processed_conversations:
            continue

        # Get the other user object
        other_user = get_object_or_404(CustomUser, pk=other_participant_id)

        # Add this conversation to our processed set
        processed_conversations.add(conversation_key)

        recent_chats_data.append({
            'property': msg.property, # Use the property object from the message
            'other_user': other_user,
            'last_message_text': msg.message,
            'last_message_timestamp': msg.timestamp,
            'link': reverse('users:chat_with_user', args=[msg.property.pk, other_user.pk]) # Use chat_with_user
        })

    # The list `recent_chats_data` is already effectively sorted by timestamp due to the initial query order.
    # No need for an additional sort here.

    context = {
        'owner_properties': owner_properties,
        'pending_bookings': pending_bookings,
        'all_owner_bookings': all_owner_bookings,
        'owner_maintenance_requests': owner_maintenance_requests,
        'recent_chats_data': recent_chats_data,
        'logo_text_color': '#7fc29b', # For header consistency
        'header_button_color': '#e91e63', # For header consistency
        'current_date': date.today(),
    }
    return render(request, 'owner_dashboard.html', context)