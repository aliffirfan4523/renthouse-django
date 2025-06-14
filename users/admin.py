from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import AdditionalOccupant, CustomUser, PaymentRecord, Property, Amenity,Booking, ChatMessage, MaintenanceRequest 

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'phone_number', 'course', 'role', 'is_active', 'is_staff', 'is_superuser')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'full_name', 'phone_number', 'course', 'role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'full_name', 'role', 'gender', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role', 'gender')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'phone_number', 'course', 'gender')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'password2', 'full_name', 'phone_number', 'course', 'role', 'gender')}
        ),
    )
    search_fields = ('username', 'email', 'full_name')
    ordering = ('username',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'house_type', 'rent', 'address', 'owner',
        'bedrooms', 'total_room', 'total_toilets','max_tenants', 'gender_preferred', 'is_available'
        # 'amenities_list' is a method on this admin class, not directly on the model
        # So we add it in list_display but define it below as a method.
    )
    list_filter = ('house_type', 'is_available', 'owner', 'bedrooms', 'total_room','total_toilets', 'max_tenants', 'gender_preferred')
    search_fields = ('title', 'address', 'description', 'owner__username')
    raw_id_fields = ('owner',)
    filter_horizontal = ('amenities',) # Use filter_horizontal for ManyToMany field in admin
    fieldsets = (
        (None, {'fields': ('title', 'house_type', 'description', 'main_image')}),
        ('Location & Rent', {'fields': ('address', 'university_nearby', 'rent')}),
        ('Capacity & Availability', {'fields': ('bedrooms', 'total_room','total_toilets', 'max_tenants', 'gender_preferred', 'is_available')}),
        ('Amenities', {'fields': ('amenities',)}), # NEW: Added amenities fieldset
        ('Owner', {'fields': ('owner',)}),
        ('Details', {'fields': ('square_footage', 'created_at')}),
    )
    readonly_fields = ('created_at',)

    # Helper method to display amenities in the list_display
    def amenities_list(self, obj):
        return ", ".join([a.name for a in obj.amenities.all()])
    amenities_list.short_description = "Amenities"


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# This class defines how AdditionalOccupant forms appear when embedded in another admin page
class AdditionalOccupantInline(admin.TabularInline): # Or admin.StackedInline for a more vertical layout
    model = AdditionalOccupant
    extra = 0 # Don't show extra empty forms by default
    can_delete = True # Allow deleting additional occupants directly from the booking admin

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'property', 'tenant', 'start_date', 'number_of_occupants',
        'full_name_on_form', 'gender_on_form', 'email_on_form', 'expected_duration_of_stay',
        'status',
    )
    list_filter = ('status', 'property__house_type', 'tenant__role', 'property__owner', 'gender_on_form')
    search_fields = ('property__title', 'tenant__username', 'property__address', 'full_name_on_form', 'email_on_form', 'student_id_number', 'university_name_on_form')
    raw_id_fields = ('property', 'tenant')
    date_hierarchy = 'start_date'
    fieldsets = (
        (None, {'fields': ('property', 'tenant', 'status')}),
        ('Booking Dates & Occupancy', {'fields': ('start_date', 'number_of_occupants', 'expected_duration_of_stay')}),
        ('Tenant Details (from Form)', {
            'fields': (
                'full_name_on_form', 'gender_on_form', 'student_id_number',
                'email_on_form', 'current_address_on_form', 'university_name_on_form',
            )
        }),
    )
    
    # IMPORTANT: Add the inline to display related AdditionalOccupant objects
    inlines = [AdditionalOccupantInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'property', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp', 'sender', 'receiver', 'property')
    search_fields = ('sender__username', 'receiver__username', 'message', 'property__title')
    raw_id_fields = ('sender', 'receiver', 'property')
    date_hierarchy = 'timestamp'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('property', 'submitted_by', 'issue_title', 'status', 'priority', 'submitted_date', 'resolved_date')
    list_filter = ('status', 'priority', 'submitted_date', 'property', 'submitted_by')
    search_fields = ('issue_title', 'issue_description', 'property__title', 'submitted_by__username')
    raw_id_fields = ('property', 'submitted_by')
    date_hierarchy = 'submitted_date'
    
    # --- NEW: PaymentRecord Admin ---
@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    # Added 'receiver_of_payment' to list_display
    list_display = ('full_name', 'email', 'amount', 'payment_date', 'user', 'booking', 'receiver_of_payment', 'transaction_id', 'payment_method')
    list_filter = ('payment_date', 'payment_method', 'user', 'booking', 'receiver_of_payment') # Added receiver to filter
    search_fields = ('full_name', 'email', 'transaction_id', 'user__username', 'booking__property__title', 'receiver_of_payment__username') # Added receiver to search
    # Added receiver_of_payment to raw_id_fields
    raw_id_fields = ('user', 'booking', 'receiver_of_payment')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date', 'transaction_id', 'receiver_of_payment') # transaction_id is generated
    fieldsets = (
        (None, {'fields': ('full_name', 'email', 'phone_number', 'amount', 'payment_method')}),
        # Added receiver_of_payment to Related Records
        ('Related Records', {'fields': ('user', 'booking', 'receiver_of_payment', 'transaction_id')}),
        ('Timestamp', {'fields': ('payment_date',)}),
    )
