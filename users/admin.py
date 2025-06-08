from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Property, Amenity,Booking, ChatMessage, MaintenanceRequest 

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

    list_display = ('id','username', 'email', 'full_name', 'role', 'is_staff', 'is_active', 'created_at', 'last_login', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'full_name', 'phone_number')
    ordering = ('username',)
    readonly_fields = ('created_at', 'last_login')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'phone_number', 'course', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'phone_number', 'course', 'role', 'is_active', 'is_staff', 'is_superuser', 'password1', 'password2'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'house_type', 'rent', 'address', 'owner', 'is_available', 'created_at')
    list_filter = ('house_type', 'is_available', 'owner__username', 'amenities')
    search_fields = ('title', 'house_type', 'address', 'course', 'owner__username')
    raw_id_fields = ('owner',)
    filter_horizontal = ('amenities',)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Booking) # NEW: Register Booking model
class BookingAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'booking_date', 'start_date', 'end_date', 'status', 'spots_booked')
    list_filter = ('status', 'property__house_type', 'tenant__role')
    search_fields = ('property__title', 'tenant__username', 'full_name_on_form', 'student_id_number')
    raw_id_fields = ('property', 'tenant') # Use raw_id_fields for FKs with many options
    readonly_fields = ('booking_date',) # Booking date is automatically set

    # Add custom actions for confirming/rejecting bookings
    actions = ['confirm_bookings', 'reject_bookings']

    def confirm_bookings(self, request, queryset):
        for booking in queryset:
            booking.confirm_booking() # Call the method on the model instance
        self.message_user(request, f"{queryset.count()} bookings confirmed.")
    confirm_bookings.short_description = "Confirm selected bookings"

    def reject_bookings(self, request, queryset):
        for booking in queryset:
            booking.reject_booking()
        self.message_user(request, f"{queryset.count()} bookings rejected.")
    reject_bookings.short_description = "Reject selected bookings"
    
@admin.register(ChatMessage) # NEW: Register ChatMessage model
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'property', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'sender__role', 'receiver__role')
    search_fields = ('sender__username', 'receiver__username', 'property__title', 'message')
    raw_id_fields = ('sender', 'receiver', 'property') # Use raw_id_fields for FKs
    readonly_fields = ('timestamp',) # Timestamp is auto_now_add

@admin.register(MaintenanceRequest) # NEW: Register MaintenanceRequest
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('issue_title', 'property', 'submitted_by', 'status', 'priority', 'submitted_date')
    list_filter = ('status', 'priority', 'submitted_date', 'property__title', 'submitted_by__username')
    search_fields = ('issue_title', 'issue_description', 'property__title', 'submitted_by__username')
    raw_id_fields = ('submitted_by', 'property') # Use raw_id_fields for FKs
    readonly_fields = ('submitted_date',)