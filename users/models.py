# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

# --- Custom User Manager (Keep as is) ---
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password) # Calls AbstractBaseUser's set_password (which handles 'password' field)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin') # Set role to admin for superuser

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

# --- Custom User Model (CRITICALLY REVISED) ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('owner', 'Owner'),
        ('admin', 'Admin'),
    )

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)

    # --- EXPLICITLY DEFINED REQUIRED AUTH FIELDS ---
    is_active = models.BooleanField(default=True,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')
    is_staff = models.BooleanField(default=False,
        help_text='Designates whether the user can log into this admin site.')
    is_superuser = models.BooleanField(default=False,
        help_text='Designates that this user has all permissions without explicitly assigning them.')


    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    course = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    created_at = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users' # This maps to your 'users' table
        verbose_name = 'User' # Changed from 'users' to 'User' for singular clarity
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    # *************************************************************************
    # IMPORTANT: REMOVE set_password and check_password overrides.
    # AbstractBaseUser provides these, and they operate correctly on its
    # internal 'password' field. Overriding them here to use 'password_hash'
    # was the source of the conflict.
    # *************************************************************************


# --- Amenity Model (Keep as is) ---
class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['name']
    def __str__(self):
        return self.name

# --- Property Model (Keep as is) ---
class Property(models.Model):
    PROPERTY_TYPES = (
        ('condominium', 'Condominium'),
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('studio', 'Studio'),
    )

    id = models.AutoField(primary_key=True)
    house_type = models.CharField(max_length=100)
    # Re-added title for clarity on detail page
    title = models.CharField(max_length=255, default="Property Listing")
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    course = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    owner = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='properties_owned')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    number_of_rooms = models.IntegerField(default=1)
    main_image = models.ImageField(upload_to='property_images/', blank=True, null=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='properties')

    # Re-added fields previously commented out to match a more complete property model
    area_sqft = models.IntegerField(blank=True, null=True)
    bathrooms = models.IntegerField(default=1)
    total_spots = models.IntegerField(default=1)
    booked_spots = models.IntegerField(default=0)


    class Meta:
        db_table = 'properties'
        verbose_name_plural = "Properties"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.address.splitlines()[0]} - RM{self.rent}"

    @property
    def available_spots(self):
        return self.total_spots - self.booked_spots

# --- NEW: Booking Model ---
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    tenant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_bookings')

    booking_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateField()
    end_date = models.DateField()
    expected_duration_of_stay = models.CharField(max_length=50, blank=True, null=True,
                                                help_text="e.g., '6 months', '1 year'")

    full_name_on_form = models.CharField(max_length=100, blank=True, null=True)
    student_id_number = models.CharField(max_length=50, blank=True, null=True)
    email_on_form = models.EmailField(max_length=100, blank=True, null=True)
    current_address_on_form = models.TextField(blank=True, null=True)
    university_name_on_form = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    spots_booked = models.IntegerField(default=1,
                                       help_text="Number of spots/rooms the user wants to book.")

    class Meta:
        verbose_name_plural = "Bookings"
        ordering = ['-booking_date']

    def __str__(self):
        return f"Booking for {self.property.title} by {self.tenant.username} - Status: {self.status}"

    # The `save` method will update booked_spots only on status change to 'confirmed'
    # MODIFIED: `save` method to correctly handle `booked_spots` increment/decrement
    def save(self, *args, **kwargs):
        is_new = self.pk is None # Check if it's a new booking instance

        if is_new:
            # For a new booking, we increment booked_spots immediately upon creation.
            # This makes `available_spots` reflect pending bookings.
            self.property.booked_spots += self.spots_booked
            self.property.save()
        else:
            # For existing bookings, retrieve the original status to detect changes
            try:
                original_booking = Booking.objects.get(pk=self.pk)
                original_status = original_booking.status
            except Booking.DoesNotExist:
                # This case should ideally not happen for existing bookings,
                # but as a fallback, treat as if no original status.
                original_status = None

            if original_status != 'confirmed' and self.status == 'confirmed':
                # Booking just changed to confirmed, increment spots
                self.property.booked_spots += self.spots_booked
                self.property.save()
            elif original_status == 'confirmed' and self.status != 'confirmed':
                # Booking changed from confirmed to something else (e.g., rejected, cancelled)
                # Decrement spots, but ensure it doesn't go below zero
                self.property.booked_spots = max(0, self.property.booked_spots - self.spots_booked)
                self.property.save()

        # Call the parent save method to save the Booking instance itself
        super().save(*args, **kwargs)


    # Example methods to change booking status
    def confirm_booking(self):
        if self.status == 'pending':
            self.status = 'confirmed'
            # The save method will handle updating property.booked_spots
            self.save()

    def reject_booking(self):
        if self.status == 'pending' or self.status == 'confirmed':
            self.status = 'rejected'
            self.save() # The save method will handle updating property.booked_spots

    def cancel_booking(self):
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.save()
            
# --- NEW: ChatMessage Model ---
class ChatMessage(models.Model):
    # Sender of the message (can be tenant/student or owner)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    # Receiver of the message (the other party in the chat)
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')

    # Context of the chat (the property being discussed)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_chats')

    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) # Optional: For read receipts

    class Meta:
        verbose_name_plural = "Chat Messages"
        ordering = ['timestamp'] # Order messages chronologically

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} on {self.property.title} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    # Who submitted the request
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='maintenance_requests')
    # For which property
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_maintenance_requests')

    # Request details
    issue_title = models.CharField(max_length=200)
    issue_description = models.TextField()
    submitted_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    # Optional: Images of the issue, resolution notes, resolution date etc.

    class Meta:
        verbose_name_plural = "Maintenance Requests"
        ordering = ['-submitted_date'] # Order by most recent requests

    def __str__(self):
        return f"Maintenance on {self.property.title} by {self.submitted_by.username}: {self.issue_title}"
