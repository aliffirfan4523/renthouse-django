from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView,DetailView 
from django.db.models import Count, Q
from .models import Property,Booking, CustomUser,  ChatMessage # Import Booking
from .forms import BookingForm, MessageForm # Import the new BookingForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin # For views that require login
from django.contrib.auth.decorators import login_required # For function-based views
from django.http import JsonResponse # NEW: Import JsonResponse for API
from django.db.models import F, Q # Make sure F is imported
class HomePropertyListView(ListView):
    # This view will fetch data from the Property model
    model = Property

    # It assumes the template is in users/templates/users/home.html
    template_name = 'home.html'

    # in your HTML template (e.g., you'll loop through 'properties').
    context_object_name = 'properties'
    # Optional: Add pagination if you want to limit the number of properties per page
    paginate_by = 8 # Display 8 properties per page, just like the UI image

    def get_queryset(self):
        # By default, ListView retrieves all objects for the model.
        # Here, we'll refine it to only show available properties, ordered by creation date.
        queryset = super().get_queryset().filter(is_available=True, total_spots__gt=F('booked_spots')).order_by('-created_at')

        # You can add filtering based on URL parameters here if you add search/filter forms later
        # Example for filtering by 'course' from URL:
        # course_filter = self.request.GET.get('course')
        # if course_filter:
        #    queryset = queryset.filter(course__iexact=course_filter)
        # 1. Price Sorting
        price_sort = self.request.GET.get('price_sort') # e.g., ?price_sort=asc or ?price_sort=desc
        if price_sort == 'asc':
            queryset = queryset.order_by('rent')
        elif price_sort == 'desc':
            queryset = queryset.order_by('-rent')
        else: # Default sorting if no price_sort is specified
            queryset = queryset.order_by('-created_at')

        # 2. Room Count Filter
        room_count = self.request.GET.get('room_count') # e.g., ?room_count=3
        if room_count:
            try:
                num_rooms = int(room_count)
                queryset = queryset.filter(number_of_rooms=num_rooms)
            except ValueError:
                pass # Ignore if room_count is not a valid integer

        # 3. House Type Filter
        house_type = self.request.GET.get('house_type') # e.g., ?house_type=condominium
        if house_type:
            # Case-insensitive filtering for house_type
            queryset = queryset.filter(house_type__iexact=house_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass current filter parameters for active styling
        context['current_price_sort'] = self.request.GET.get('price_sort', '')
        context['current_room_count'] = self.request.GET.get('room_count', '')
        context['current_house_type'] = self.request.GET.get('house_type', '')
        context['current_min_rent'] = self.request.GET.get('min_rent', '')
        context['current_max_rent'] = self.request.GET.get('max_rent', '')

        # Pass property type choices for the dropdown in the filter modal
        context['property_type_choices'] = Property.PROPERTY_TYPES
        return context

        return queryset

class PropertyDetailView(DetailView):
    model = Property
    template_name = 'property_details.html' # New template for detail page
    context_object_name = 'property' # Variable name in the template

    def get_queryset(self):
        # Prefetch related amenities and owner for efficiency
        return super().get_queryset().select_related('owner').prefetch_related('amenities')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add more context data here if needed for reviews, etc.
        # For reviews, you'd typically have a separate Review model with ForeignKey to Property
        # context['reviews'] = self.object.reviews.all() # Assuming 'reviews' related_name
        return context

# --- Modified home_view ---
#def home_view(request):
    """
    Renders the home page, which now directly displays property listings.
    This effectively uses the PropertyListView's logic but renders the property_list.html template.
    """

#    view = PropertyListView()
#    view.request = request # Pass the current request to the view
#    queryset = view.get_queryset() # Get the filtered queryset

    # Manually apply pagination if needed (ListView handles this automatically)
    # For simplicity, if you want full pagination, it's often easier to just map the URL
    # to PropertyListView.as_view() directly.
    # However, if home.html is *exactly* property_list.html content, we can just pass the queryset.

 #   context = {
 #       'properties': queryset,
        # If you need pagination controls on home.html, you'd need to manually
        # create a Paginator object and pass 'page_obj' and 'is_paginated'.
        # For a truly seamless home page as the main property list,
        # using PropertyListView directly for the '/' path is usually better.
 #   }
 #   return render(request, 'home.html', context) # Renders the property_list template

# --- NEW: Booking View ---
@login_required # Ensures only logged-in users can access this page
def book_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    # Prevent booking if no spots are available
    if property_obj.available_spots <= 0:
        messages.error(request, f"Sorry, {property_obj.title} has no spots available for booking.")
        return redirect('users:property_detail', pk=property_obj.pk)

    if request.method == 'POST':
        form = BookingForm(request.POST, request=request, property_obj=property_obj)
        if form.is_valid():
            booking = form.save(commit=False) # Create booking object but don't save to DB yet
            booking.property = property_obj
            booking.tenant = request.user # Set the current logged-in user as the tenant
            booking.status = 'pending' # Default status
            booking.save()

            # The clean method on the model already checks available_spots before saving,
            # but if we wanted to increment booked_spots immediately after save, it should be done here
            # or by overriding the model's save method for 'confirmed' status.
            # For 'pending' status, we often wait for admin approval to increment booked_spots.
            # The model's save method has logic for 'confirmed' status to increment booked_spots.

            messages.success(request, f"Your booking for {property_obj.title} has been submitted successfully and is pending confirmation.")
            return redirect('users:move_in_notice', booking_pk=booking.pk)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        # For GET request, instantiate an empty form, pre-filling user data
        form = BookingForm(request=request, property_obj=property_obj)

    context = {
        'form': form,
        'property': property_obj,
        'logo_text_color': '#7fc29b', # Example color from style.css for dynamic styling
        'header_button_color': '#e91e63', # Example color
    }
    return render(request, 'booking_form.html', context)

# ... (login_view, logout_view, register_user_view - keep as is, these are in login/views.py) ...

# --- NEW: Move-in Notice View ---
@login_required
def move_in_notice(request, booking_pk):
    # Get the specific booking object
    booking = get_object_or_404(Booking, pk=booking_pk, tenant=request.user)

    # You can pass additional context here if needed
    context = {
        'booking': booking,
        'property': booking.property, # Access the related property
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
        # You might want to pass a generic "contact owner" URL or logic later
    }
    return render(request, 'move_in_notice.html', context)

# --- MODIFIED: chat_view ---
@login_required
def chat_view(request, property_pk, other_user_pk):
    property_obj = get_object_or_404(Property, pk=property_pk)
    target_user = get_object_or_404(CustomUser, pk=other_user_pk)

    # Security check: Ensure the current user is either the property owner OR the person chatting with the owner
    is_authorized = False

    # Scenario 1: Landlord (logged-in user) is chatting with a tenant/student
    if request.user == property_obj.owner and (target_user.role == 'student' or target_user.role == 'tenant'):
        is_authorized = True
    # Scenario 2: Tenant/Student (logged-in user) is chatting with the landlord (property owner)
    elif (request.user.role == 'student' or request.user.role == 'tenant') and target_user == property_obj.owner:
        is_authorized = True
    # Scenario 3: Admin access (optional)
    elif request.user.is_superuser: # Admins can view any chat
        is_authorized = True

    if not is_authorized:
        messages.error(request, "You are not authorized to view this chat.")
        return redirect('users:home')

    # Determine if the currently logged-in user IS the owner of this property
    is_current_user_owner = (request.user == property_obj.owner)

    # Filter messages relevant to this conversation (between current user and owner, about this property)
    chat_messages = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=target_user, property=property_obj) |
        Q(sender=target_user, receiver=request.user, property=property_obj)
    ).order_by('timestamp')

    # Handle sending new messages
     # Handle sending new messages
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_content = form.cleaned_data['message']
            # Determine receiver based on who the 'other_user' is
            # If current user is owner, send to target_user (tenant/student)
            # If current user is tenant/student, send to property owner
            actual_receiver = target_user if request.user == property_obj.owner else property_obj.owner

            ChatMessage.objects.create(
                sender=request.user,
                receiver=actual_receiver, # The calculated receiver
                property=property_obj,
                message=message_content
            )
            messages.success(request, "Message sent!")
            # Redirect back to the same chat view to prevent form resubmission
            return redirect('users:chat_with_user', property_pk=property_pk, other_user_pk=other_user_pk)
        else:
            messages.error(request, "Please correct the message error.")
    else:
        form = MessageForm()

    context = {
        'property': property_obj,
        'target_user': target_user, # Pass the 'other' person in chat for displaying their name
        'chat_messages': chat_messages,
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
        'is_current_user_owner': is_current_user_owner,
    }
    return render(request, 'chat_page.html', context)

# --- NEW: API Endpoint for Recent Chats ---
@login_required
def recent_chats_api_view(request):
    user = request.user

    # Get recent chat messages where the current user is either sender or receiver
    # This is a bit complex: we want the *last* message for each unique conversation.
    # A conversation is defined by (property, other_participant).

    # First, get all messages involving the current user, ordered by timestamp desc
    all_user_messages = ChatMessage.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-timestamp')

    conversations = {} # Key: (property_id, other_user_id) -> LastMessage

    for msg in all_user_messages:
        # Determine the other participant in this specific message context
        other_participant = msg.sender if msg.receiver == user else msg.receiver

        # Skip if the other_participant is the current user themselves (self-chat)
        if other_participant == user:
            continue

        # Create a unique key for this conversation
        # Ensures that a chat about Property A with User X is distinct from Property B with User X
        conversation_key = (msg.property.pk, other_participant.pk)

        # If this conversation key hasn't been seen yet, or if this message is newer, store it
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'property_id': msg.property.pk,
                'property_title': msg.property.title,
                'property_main_image': msg.property.main_image.url if msg.property.main_image else None,
                'other_user_id': other_participant.pk,
                'other_user_username': other_participant.username,
                'other_user_full_name': other_participant.full_name or other_participant.username,
                'last_message': msg.message,
                'last_message_timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'last_message_is_read': msg.is_read,
                'last_message_sender_is_me': (msg.sender == user),
            }

    # Convert the dictionary values to a list for JSON response
    recent_chats_list = list(conversations.values())

    return JsonResponse({'chats': recent_chats_list})