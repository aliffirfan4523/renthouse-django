from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q # Used for complex queries
# IMPORTANT: Import AdditionalOccupant model
from .models import PaymentRecord, Property, CustomUser, Booking, ChatMessage, AdditionalOccupant 
# IMPORTANT: Ensure AdditionalOccupantFormSet is imported (from forms.py)
from .forms import AdditionalOccupantFormSet, BookingForm, MessageForm, PaymentForm 
from django.contrib import messages # For Django messages framework
from django.contrib.auth.mixins import LoginRequiredMixin # For class-based view login requirement
from django.contrib.auth.decorators import login_required # For function-based view login requirement
from django.urls import reverse # To dynamically get URL patterns
from django.http import HttpResponse, JsonResponse # For API responses
from datetime import date, datetime # Import date and datetime for validation
from django.utils import timezone  # Correct import for timezone.now()
import pdfkit
from django.template.loader import render_to_string # Import render_to_string

# --- HomePropertyListView ---
class HomePropertyListView(ListView):
    """
    A view to display a list of available properties.
    Supports searching by query and filtering by house type and gender preference.
    """
    model = Property
    template_name = 'home.html' # Assuming your home.html is in users/templates/users/
    context_object_name = 'properties'
    paginate_by = 12 # Number of properties per page

    def get_queryset(self):
        """
        Retrieves the queryset of properties, applying search and filter criteria.
        """
        # Start with all available properties, ordered by creation date (newest first)
        queryset = Property.objects.filter(is_available=True).order_by('-created_at')

        # Apply search query filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | # Search in property title
                Q(address__icontains=query) | # Search in property address
                Q(university_nearby__icontains=query) | # Search in university nearby field
                Q(description__icontains=query) # Search in description
            ).distinct() # Use distinct to avoid duplicate results if a property matches multiple Q conditions

        # Apply house type filter
        house_type_filter = self.request.GET.get('house_type')
        if house_type_filter and house_type_filter != '': # Check for empty string, not 'all'
            queryset = queryset.filter(house_type=house_type_filter)

        # Apply gender preference filter (NEW)
        gender_preference_filter = self.request.GET.get('gender_preference')
        if gender_preference_filter and gender_preference_filter != '': # Check for empty string ('Any Gender')
            # Assuming 'gender_preferred' is the field on your Property model
            # You might need to adjust 'gender_preferred' to your actual field name
            queryset = queryset.filter(gender_preferred=gender_preference_filter)

        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds additional context variables to the template.
        """
        context = super().get_context_data(**kwargs)
        
        # Pass house type choices for filter dropdown
        context['property_type_choices'] = Property.HOUSE_TYPE_CHOICES 
        context['current_house_type'] = self.request.GET.get('house_type', '') # Keep selected filter active

        # Pass gender choices for filter dropdown (NEW)
        context['property_gender_choices'] = Property.GENDER_PREFERENCE_CHOICES
        context['current_gender_preference'] = self.request.GET.get('gender_preference', '') # Keep selected filter active

        context['current_room_count'] = self.request.GET.get('room_count', '') # Keep room count if set
        context['search_query'] = self.request.GET.get('q', '') # Keep search query in the input field
        context['logo_text_color'] = '#7fc29b' # Example dynamic styling
        context['header_button_color'] = '#e91e63' # Example dynamic styling
        return context


# --- PropertyDetailView ---
class PropertyDetailView(DetailView):
    """
    A view to display the detailed information of a single property.
    """
    model = Property
    template_name = 'property_details.html'
    context_object_name = 'property' # The variable name to use in the template

    def get_context_data(self, **kwargs):
        """
        Adds additional context variables to the template.
        """
        context = super().get_context_data(**kwargs)
        context['logo_text_color'] = '#7fc29b'
        context['header_button_color'] = '#e91e63'
        return context


# --- book_property view (MODIFIED: Corrected logic for saving AdditionalOccupant) ---
@login_required
def book_property(request, pk):
    property_instance = get_object_or_404(Property, pk=pk)
    max_tenants_value = int(getattr(property_instance, 'max_tenants', 1))

    if not request.user.is_authenticated or request.user.role != 'student':
        messages.error(request, "Please log in as a student to book a property.")
        return redirect('login:login')

    # NEW VALIDATION: Restrict user from booking more than 1 house
    # Check for existing 'pending' or 'confirmed' bookings by the current user
    existing_bookings = Booking.objects.filter(
        tenant=request.user,
        status__in=['pending', 'confirmed']
    )
    if existing_bookings.exists():
        messages.error(request, "You already have a pending or confirmed booking. You can only have one active booking at a time.")
        # Redirect to their dashboard or home page
        if request.user.role == 'student':
            return redirect('tenant:tenant_home')
        else: # For superusers, they might not have a specific dashboard like students
            return redirect('users:home')
        
    if request.method == 'POST':
        # Always initialize forms and formsets with POST data on submission
        form = BookingForm(request.POST)
        occupant_formset = AdditionalOccupantFormSet(
            request.POST,
            prefix='occupants',
            queryset=AdditionalOccupant.objects.none() # For new occupants
        )

        # Default context for re-rendering with errors
        context_for_errors = {
            'property': property_instance,
            'form': form,
            'occupant_formset': occupant_formset,
            'GENDER_CHOICES': CustomUser.GENDER_CHOICES,
            'MAX_TENANTS_JS': max_tenants_value,
        }

        if form.is_valid() and occupant_formset.is_valid():
            total_occupants_from_formset = 0
            for form_in_set in occupant_formset:
                if form_in_set.cleaned_data and not form_in_set.cleaned_data.get('DELETE'):
                    total_occupants_from_formset += 1

            total_occupants = 1 + total_occupants_from_formset # Primary booker + valid additional occupants

            if total_occupants > max_tenants_value:
                form.add_error(None, f"This property can accommodate a maximum of {max_tenants_value} tenant(s). You have {total_occupants} total occupants in your booking.")
                # Return render with the already populated forms/formset
                return render(request, 'booking_form.html', context_for_errors)
            else:
                booking = form.save(commit=False)
                booking.property = property_instance
                booking.tenant = request.user
                booking.number_of_occupants = total_occupants
                booking.save()

                for form_in_set in occupant_formset:
                    if form_in_set.cleaned_data and not form_in_set.cleaned_data.get('DELETE'):
                        occupant_instance = form_in_set.save(commit=False)
                        occupant_instance.booking = booking
                        occupant_instance.save()

                property_instance.is_available = False
                property_instance.save()
                messages.success(request, 'Your booking has been successfully submitted and the property is now marked as unavailable!') 
                return redirect('users:move_in_notice', booking_pk=booking.pk)
        else:
            # If main form or formset is not valid, print errors for debugging and re-render
            print("Form is NOT valid. Errors:")
            print("Main Form Errors:", form.errors)
            if form.non_field_errors:
                print("Main Form Non-Field Errors:", form.non_field_errors)
            
            print("\nOccupant Formset is NOT valid. Errors:")
            print("Formset Non-Form Errors:", occupant_formset.non_form_errors())
            for i, form_in_set in enumerate(occupant_formset):
                if form_in_set.errors:
                    print(f"Form {i} Errors:", form_in_set.errors)
            
            # Return render with the already populated forms/formset
            return render(request, 'booking_form.html', context_for_errors)

    else: # GET request (initial page load)
        form = BookingForm(initial={
            'full_name_on_form': request.user.full_name,
            'gender_on_form': request.user.gender,
            'email_on_form': request.user.email,
        })
        occupant_formset = AdditionalOccupantFormSet(
            prefix='occupants',
            queryset=AdditionalOccupant.objects.none()
        )

    context = {
        'property': property_instance,
        'form': form,
        'occupant_formset': occupant_formset,
        'GENDER_CHOICES': CustomUser.GENDER_CHOICES,
        'MAX_TENANTS_JS': max_tenants_value,
    }
    return render(request, 'booking_form.html', context)


# --- move_in_notice view (MODIFIED: Displays additional occupant details) ---
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
    return render(request, 'move_in_notice.html', context)


# --- chat_view view ---
@login_required
def chat_view(request, property_pk, other_user_pk):
    """
    Handles the display and sending of chat messages between a tenant and a owner for a specific property.
    Ensures that only authorized users (owner-tenant pairs for a property, or superusers) can access the chat.
    """
    property_obj = get_object_or_404(Property, pk=property_pk)
    target_user = get_object_or_404(CustomUser, pk=other_user_pk)

    is_authorized = False
    # Scenario 1: owner (logged-in user) is chatting with a student (target user)
    if request.user == property_obj.owner and (target_user.role == 'student'):
        is_authorized = True
    # Scenario 2: Student (logged-in user) is chatting with the owner (property owner)
    elif (request.user.role == 'student') and target_user == property_obj.owner:
        is_authorized = True
    # Scenario 3: Superuser can access any chat
    elif request.user.is_superuser:
        is_authorized = True

    if not is_authorized:
        messages.error(request, "You are not authorized to view this chat.")
        return redirect('users:home') # Redirect to a safe page if not authorized

    # Determine if the current user is the owner of the property (for UI purposes)
    is_current_user_owner = (request.user == property_obj.owner)

    # Retrieve chat messages between the two users for this specific property
    chat_messages = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=target_user, property=property_obj) |
        Q(sender=target_user, receiver=request.user, property=property_obj)
    ).order_by('timestamp') # Order messages by timestamp

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_content = form.cleaned_data['message']
            # Determine the actual receiver based on who the current user is
            actual_receiver = target_user if request.user == property_obj.owner else property_obj.owner

            ChatMessage.objects.create(
                sender=request.user,
                receiver=actual_receiver,
                property=property_obj,
                message=message_content
            )
            # Add a success message (optional, but good for user feedback)
            messages.success(request, "Message sent!")
            # Redirect back to the same chat page to prevent form resubmission
            return redirect('users:chat_with_user', property_pk=property_pk, other_user_pk=other_user_pk)
        else:
            # If form is not valid, add an error message
            messages.error(request, "Please correct the message error.")
    else: # GET request: Initialize an empty message form
        form = MessageForm()

    context = {
        'property': property_obj,
        'target_user': target_user,
        'chat_messages': chat_messages,
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
        'is_current_user_owner': is_current_user_owner,
    }
    return render(request, 'chat_page.html', context)


# --- recent_chats_api_view ---
@login_required
def recent_chats_api_view(request):
    """
    API endpoint to fetch recent chat conversations for the logged-in user.
    Returns a JSON response with chat details.
    """
    user_id = request.user.id
    # Fetch all messages involving the user, ordered by most recent first
    all_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    chats_data = []
    processed_conversations = set()

    for msg in all_messages:
        # Determine the 'other' participant in the conversation
        other_user = msg.sender if msg.receiver == request.user else msg.receiver

        # Skip if the 'other user' is the current user themselves (self-chat case)
        if other_user == request.user:
            continue

        # Create a canonical key for the conversation (property_id, min_user_id, max_user_id)
        user_ids = sorted([request.user.id, other_user.id])
        conversation_key = (msg.property.id if msg.property else None, user_ids[0], user_ids[1])

        if conversation_key in processed_conversations:
            continue  # Already processed this conversation

        processed_conversations.add(conversation_key)

        chats_data.append({
            'property_id': msg.property.pk if msg.property else None,
            'property_title': msg.property.title if msg.property else 'General Chat',
            'property_main_image': msg.property.main_image.url if msg.property and msg.property.main_image else None,
            'other_user_id': other_user.pk,
            'other_user_username': other_user.username,
            'other_user_full_name': other_user.full_name or other_user.username,
            'last_message': msg.message,
            'last_message_timestamp': msg.timestamp.isoformat(),
            'last_message_sender_is_me': msg.sender == request.user,
        })

    # Sort the final list by the timestamp of the last message in descending order (most recent first)
    chats_data.sort(key=lambda x: x['last_message_timestamp'], reverse=True)

    return JsonResponse({'chats': chats_data})

# --- PAYMENT VIEWS ---

# --- PAYMENT VIEWS ---

def payment_view(request):
    """
    Handles the payment form submission and saves the payment record to the database.
    Allows selection of receiver and specific booking.
    The transaction ID is generated based on datetime, payment_id, and user_id.
    """
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        
        # Manually set querysets for ModelChoiceFields on POST if form is not bound
        # This is important if form is invalid and needs to be re-rendered
        form.fields['receiver_of_payment'].queryset = CustomUser.objects.filter(Q(role='owner'))
        # Dynamically set booking queryset based on user role
        if request.user.is_authenticated and request.user.role == 'student':
            form.fields['booking'].queryset = Booking.objects.filter(
                Q(tenant=request.user) & Q(status__in=['confirmed', 'completed'])
            ).order_by('-start_date')
        elif request.user.is_authenticated and (request.user.role == 'owner' or request.user.role == 'admin'):
            form.fields['booking'].queryset = Booking.objects.filter(
                Q(property__owner=request.user) & Q(status__in=['confirmed', 'completed'])
            ).order_by('-start_date')
        else: # For anonymous users, no booking association is made through the form
            form.fields['booking'].queryset = Booking.objects.none()


        if form.is_valid():
            payment_record = form.save(commit=False)
            
            # Set the user who made the payment if authenticated
            if request.user.is_authenticated:
                payment_record.user = request.user
            
            # booking and receiver_of_payment are now directly from form.cleaned_data
            # because they are ModelChoiceFields
            payment_record.booking = form.cleaned_data.get('booking')
            payment_record.receiver_of_payment = form.cleaned_data.get('receiver_of_payment')

            payment_record.save() # Save the payment record to get its primary key (ID)

            # Generate transaction ID after saving to get the payment_record.id
            now = timezone.now()
            user_id_str = str(request.user.pk) if request.user.is_authenticated else 'GUEST'
            transaction_id_parts = [
                now.strftime('%Y%m%d%H%M%S%f'), # Datetime (Y-M-D H-M-S microseconds)
                str(payment_record.pk),       # PaymentRecord ID
                user_id_str                   # User ID or GUEST
            ]
            payment_record.transaction_id = "_".join(transaction_id_parts)
            payment_record.save(update_fields=['transaction_id']) # Save just the transaction_id

            messages.success(request, "Payment successful! Here is your receipt.")
            return redirect('users:receipt', pk=payment_record.pk)
        else:
            messages.error(request, "Please correct the errors in the payment form.")
    else: # GET request
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['full_name'] = request.user.full_name or ''
            initial_data['email'] = request.user.email or ''
            initial_data['phone_number'] = request.user.phone_number or ''
        
        form = PaymentForm(initial=initial_data)

        # Set queryset for receiver_of_payment field
        form.fields['receiver_of_payment'].queryset = CustomUser.objects.filter(Q(role='owner'))

        # Dynamically set queryset for booking field based on user role
        if request.user.is_authenticated and request.user.role == 'student':
            form.fields['booking'].queryset = Booking.objects.filter(
                Q(tenant=request.user) & Q(status__in=['confirmed', 'completed'])
            ).order_by('-start_date')
        elif request.user.is_authenticated and (request.user.role == 'owner' or request.user.role == 'admin'):
            # owner/Admins can see bookings for their properties
            form.fields['booking'].queryset = Booking.objects.filter(
                Q(property__owner=request.user) & Q(status__in=['confirmed', 'completed'])
            ).order_by('-start_date')
        else:
            form.fields['booking'].queryset = Booking.objects.none() # No bookings for anonymous users

    context = {
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'payment.html', context)


def receipt_view(request, pk):
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


def receipt_pdf_view(request, pk):
    """
    Generates a PDF receipt for a PaymentRecord using pdfkit (wkhtmltopdf).
    """
    try:
        pass
    except ImportError:
        messages.error(request, "PDF generation libraries not installed. Please install pdfkit (pip install pdfkit) and wkhtmltopdf.")
        return redirect('users:receipt', pk=pk)

    payment_record = get_object_or_404(PaymentRecord, pk=pk)

    template_path = 'receipt.html'
    context = {'payment_record': payment_record}

    html = render_to_string(template_path, context)

    options = {
        'enable-local-file-access': None,
        'encoding': "UTF-8",
    }

    try:
        pdf = pdfkit.from_string(html, False, options=options)
    except Exception as e:
        messages.error(request, f"Error generating PDF: {e}. Ensure wkhtmltopdf is installed and in your system's PATH. You might need to configure its path in options.")
        return redirect('users:receipt', pk=pk)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment_record.pk}.pdf"'
    return response

def signup(request, pk):
    return render(request, "signup.html")

