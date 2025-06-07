from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView,DetailView 
from django.db.models import Count, Q
from .models import Property,Booking, CustomUser,  ChatMessage # Import Booking
from .forms import BookingForm, MessageForm # Import the new BookingForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin # For views that require login
from django.contrib.auth.decorators import login_required # For function-based views

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
        queryset = super().get_queryset().filter(is_available=True).order_by('-created_at')

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

@login_required
def chat_view(request, property_pk, owner_pk):
    # Ensure current user is involved in the chat (either as sender or receiver)
    # and that the property exists.
    property_obj = get_object_or_404(Property, pk=property_pk)
    owner_obj = get_object_or_404(CustomUser, pk=owner_pk) # The property owner/host

    # Ensure the current user is either the property owner OR a user intending to chat with the owner
    if not (request.user == owner_obj or request.user.is_authenticated):
        messages.error(request, "You are not authorized to view this chat.")
        return redirect('users:home') # Or appropriate redirect

    # Determine the other participant in the chat (the user who is NOT the current user)
    other_participant = owner_obj if request.user != owner_obj else property_obj.owner # Should always be owner_obj here

    # Filter messages relevant to this conversation (between current user and owner, about this property)
    chat_messages = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=owner_obj, property=property_obj) |
        Q(sender=owner_obj, receiver=request.user, property=property_obj)
    ).order_by('timestamp')

    # Handle sending new messages
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message_content = form.cleaned_data['message']
            ChatMessage.objects.create(
                sender=request.user,
                receiver=owner_obj,
                property=property_obj,
                message=message_content
            )
            messages.success(request, "Message sent!")
            # Redirect to GET to prevent form resubmission
            return redirect('users:chat_with_owner', property_pk=property_pk, owner_pk=owner_pk)
        else:
            messages.error(request, "Please correct the message error.")
    else:
        form = MessageForm() # Empty form for GET request

    context = {
        'property': property_obj,
        'owner': owner_obj, # The owner of the property
        'chat_messages': chat_messages,
        'form': form,
        'logo_text_color': '#7fc29b',
        'header_button_color': '#e91e63',
    }
    return render(request, 'chat_page.html', context)