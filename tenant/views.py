from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Booking, MaintenanceRequest, Property, ChatMessage
from django.db.models import Q
from django.urls import reverse
import datetime

@login_required
def tenant_dashboard(request):
    """
    Displays the tenant dashboard with current rental, upcoming/past bookings,
    maintenance requests, and recent chats.
    Accessible only by users with the 'student' role (who are considered tenants).
    """
    # Authorization check: Only students (or superusers) can access this dashboard
    if not (request.user.role == 'student' or request.user.is_superuser):
        messages.error(request, "Access Denied. You must be a student to view this dashboard.")
        return redirect('users:home')

    # --- Current Rental ---
    current_rental = Booking.objects.filter(
        tenant=request.user,
        status='confirmed',
    ).order_by('-start_date').first()

    # --- Upcoming Bookings ---
    # --- All Bookings (Current, Upcoming, Past) ---

    all_bookings = Booking.objects.filter(
        tenant=request.user
    ).order_by('-start_date').filter(
        Q(status='confirmed') | Q(status='pending') | Q(status='rejected'))

    # --- Past Bookings (FIXED: Using Q objects for all filter conditions) ---
    past_bookings = Booking.objects.filter(
        Q(tenant=request.user) &
        Q(status='completed')
    ).exclude(id=current_rental.id if current_rental else None).order_by('-start_date')


    # --- My Maintenance Requests ---
    my_maintenance_requests = MaintenanceRequest.objects.filter(
        submitted_by=request.user
    ).order_by('-submitted_date')


    # --- Recent Chats ---
    recent_chats_data = []
    all_tenant_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp').select_related('property', 'sender', 'receiver')

    processed_conversations = set()

    for msg in all_tenant_messages:
        other_participant = msg.sender if msg.receiver == request.user else msg.receiver

        if other_participant == request.user:
            continue

        conversation_key = (msg.property.pk if msg.property else None, other_participant.pk)

        if conversation_key in processed_conversations:
            continue

        processed_conversations.add(conversation_key)

        recent_chats_data.append({
            'property': msg.property,
            'other_user': other_participant,
            'last_message_text': msg.message,
            'last_message_timestamp': msg.timestamp,
            'link': reverse('users:chat_with_user', args=[msg.property.pk if msg.property else 0, other_participant.pk])
        })

    context = {
        'current_rental': current_rental,
        'all_bookings': all_bookings,
        'past_bookings': past_bookings,
        'my_maintenance_requests': my_maintenance_requests,
        'recent_chats_data': recent_chats_data,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'tenant/tenant_dashboard.html', context)

@login_required
def cancel_booking(request, booking_id):
    """
    Allows a tenant to cancel their booking if it is not already completed or cancelled.
    Assumes confirmation is handled via JavaScript, so no confirmation page is rendered.
    """
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)
    if booking.status in ['completed', 'cancelled']:
        messages.error(request, "This booking cannot be cancelled.")
        return redirect('tenant:tenant_home')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Booking cancelled successfully.")
        return redirect('tenant:tenant_home')

    # If not POST, just redirect (no confirmation page)
    return redirect('tenant:tenant_home')

@login_required
def move_in_notice(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)
    if request.user != booking.tenant and not request.user.is_superuser:
        messages.error(request, "Access Denied. You are not authorized to view this notice.")
        return redirect('users:home')

    # Fetch additional occupants related to this booking
    additional_occupants = booking.additional_occupants.all() # Using the related_name defined in models.py

    context = {
        'booking': booking,
        'property': booking.property,
        'additional_occupants': additional_occupants, # Pass additional occupants to the template
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'tenant/move_in_notice.html', context)