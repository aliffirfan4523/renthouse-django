from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import Booking, MaintenanceRequest, PaymentRecord, Property, ChatMessage
from django.db.models import Q
from .forms import MaintenanceRequestForm
from django.urls import reverse
from django.utils import timezone
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


    # --- Maintenance Request Form Handling ---
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
                
        # Check if the delete button is clicked
        if 'delete_request' in request.POST:
            maintenance_request_id = request.POST.get('delete_request')
            maintenance_request = MaintenanceRequest.objects.filter(id=maintenance_request_id, submitted_by=request.user).first()
            
            if maintenance_request:
                maintenance_request.delete()  # Delete the maintenance request
                messages.success(request, "Maintenance request deleted successfully.")
                return redirect('tenant:tenant_home')
            
        if form.is_valid():
            # Save the maintenance request with the current property
            maintenance_request = form.save(commit=False)
            maintenance_request.submitted_by = request.user  # Assign the current user
            maintenance_request.status = 'pending'  # Default status
            maintenance_request.submitted_date = timezone.now()  # Default date
            maintenance_request.property = current_rental.property  # Use the current rental's property
            maintenance_request.save()
            messages.success(request, "Maintenance request submitted successfully.")
            return redirect('tenant:tenant_home')
        else:
            print("Form is not valid")
            print(form.errors)  # This will print any errors from form validation
    else:
        form = MaintenanceRequestForm()

        # Fetch all maintenance requests for the current user
    my_maintenance_requests = MaintenanceRequest.objects.filter(submitted_by=request.user).order_by('-submitted_date')

    context = {
        'current_rental': current_rental,
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }

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

    # --- My Payment History (NEW) ---
    my_payments = PaymentRecord.objects.filter(
        user=request.user # Payments made by the current user
    ).order_by('-payment_date').select_related('booking', 'receiver_of_payment')


    context = {
        'current_rental': current_rental,
        'all_bookings': all_bookings,
        'past_bookings': past_bookings,
        'my_maintenance_requests': my_maintenance_requests,
        'recent_chats_data': recent_chats_data,
        'my_payments': my_payments, # Add payment history to context
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


@login_required
def delete_maintenance_request(request, request_id):
    # Fetch the maintenance request object by id
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # Ensure the current user is the one who created the request
    if maintenance_request.submitted_by != request.user:
        messages.error(request, "You are not authorized to delete this request.")
        return redirect('tenant:tenant_home')  # Redirect if user is not the one who created the request

    # Delete the maintenance request
    maintenance_request.delete()

    messages.success(request, "Maintenance request deleted successfully.")
    return redirect('tenant:tenant_home')