# users/models.py

from django import forms
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
# --- Custom User Model (MODIFIED: Added 'date_joined' field) ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('owner', 'Owner'),
        ('admin', 'Admin'),
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    # NEW: Define specific course choices for UniKL MIIT
    COURSE_CHOICES = (
        ('', 'Select your course (UniKL MIIT)'), # Optional: a default empty choice
        ('BSE', 'Bachelor of Software Engineering with Honours'),
        ('BIOT', 'Bachelor in Information Technology'),
        ('BCSS', 'Bachelor of Information Technology (Hons.) in Computer System Security'),
        ('BIS', 'Bachelor of Information System with Honours'),
        ('BNS', 'Bachelor of Computer Engineering Technology (Networking Systems)'),
        ('other', 'Other'), # For cases not listed or non-UniKL MIIT students
    )
    
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)

    is_active = models.BooleanField(default=True,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')
    is_staff = models.BooleanField(default=False,
        help_text='Designates whether the user can log into this admin site.')
    is_superuser = models.BooleanField(default=False,
        help_text='Designates that this user has all permissions without explicitly assigning them.')

    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    course = models.CharField(
        max_length=100,
        choices=COURSE_CHOICES, # Apply the new choices
        blank=True,
        null=True,
        default='' # Set a default empty string for the choice field
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Gender"
    )


    created_at = models.DateTimeField(default=timezone.now)
    # NEW FIELD: date_joined
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='date joined')


    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
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
# --- Property Model (MODIFIED: Add 'max_tenants' field) ---
# --- Property Model (MODIFIED: Removed total_spots, available_spots. KEPT max_tenants) ---
# --- Property Model (MODIFIED: Added total_room field, number_of_rooms renamed to bedrooms) ---class Property(models.Model):
# --- Property Model (MODIFIED: Added gender_preferred field) ---
class Property(models.Model):
    HOUSE_TYPE_CHOICES = [
        ('Condominium', 'Condominium'),
        ('House', 'House'),
        ('Apartment', 'Apartment'),
        ('Studio', 'Studio'),
    ]
    GENDER_PREFERENCE_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    id = models.AutoField(primary_key=True)
    house_type = models.CharField(max_length=50, choices=HOUSE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    university_nearby = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField()
    bedrooms = models.IntegerField(default=1, help_text="Number of bedrooms in the property.")
    total_room = models.IntegerField(default=3, help_text="Total number of rooms (including bedrooms, living room, kitchen, etc.).")
    total_toilets = models.IntegerField(default=2, help_text="Total number of toilets/bathrooms in the property.") # NEW FIELD
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    square_footage = models.IntegerField(blank=True, null=True)
    main_image = models.ImageField(upload_to='property_images/', blank=True, null=True)
    max_tenants = models.IntegerField(default=1, help_text="Maximum number of occupants allowed in this property.")

    is_available = models.BooleanField(default=True, help_text="Is the property currently available for booking as a whole unit?")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_properties')

    gender_preferred = models.CharField(
        max_length=20,
        choices=GENDER_PREFERENCE_CHOICES,
        default='any',
        help_text="Preferred gender for tenants for this property."
    )
    # NEW FIELD: ManyToMany relationship with Amenity
    amenities = models.ManyToManyField('Amenity', blank=True, related_name='properties')


    class Meta:
        verbose_name_plural = "Properties"

    def __str__(self):
        return self.title

# --- Booking Model (MODIFIED: Added default='' to certain fields) ---
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    tenant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_bookings')
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    number_of_occupants = models.IntegerField(default=1, help_text="Number of people included in this booking.")

    # MODIFIED: Added default='' for fields that are typically required in forms
    full_name_on_form = models.CharField(max_length=100, default='', help_text="Full name as entered on the booking form.")
    gender_on_form = models.CharField(
        max_length=20,
        choices=CustomUser.GENDER_CHOICES,
        blank=True, # Keep blank=True to allow empty on creation/admin if needed, but form should require it
        null=True, # Keep null=True to allow null for existing records before migration, will be updated to default
        default='prefer_not_to_say', # Provide a default for migrations
        help_text="Gender as selected on the booking form."
    )
    student_id_number = models.CharField(max_length=50, blank=True, null=True, default='', help_text="Student ID / Matriculation Number from the form.")
    email_on_form = models.EmailField(max_length=100, default='', help_text="Email address as entered on the booking form.")
    current_address_on_form = models.TextField(default='', help_text="Current address as entered on the booking form.")
    university_name_on_form = models.CharField(max_length=200, blank=True, null=True, default='', help_text="University/College name from the form.")
    expected_duration_of_stay = models.CharField(max_length=100, default='', help_text="Expected duration of stay from the form.")

    class Meta:
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"Booking for {self.property.title} by {self.full_name_on_form} (ID: {self.pk})"


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
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submitted_maintenance_requests')
    issue_title = models.CharField(max_length=200)
    issue_description = models.TextField()
    submitted_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Maintenance Requests"
        ordering = ['-submitted_date']

    def __str__(self):
        return f"Maintenance for {self.property.title}: {self.issue_title}"
    
# --- NEW MODEL: AdditionalOccupant ---
class AdditionalOccupant(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='additional_occupants')
    full_name = models.CharField(max_length=100)
    student_id_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(
        max_length=20,
        choices=CustomUser.GENDER_CHOICES,
        blank=True,
        null=True,
        default='prefer_not_to_say'
    )

    class Meta:
        verbose_name_plural = "Additional Occupants"
        unique_together = ('booking', 'email') # Prevent duplicate occupants for the same booking

    def __str__(self):
        return f"Occupant: {self.full_name} for Booking {self.booking.pk}"


# --- NEW FORM: PropertyForm ---
class PropertyForm(forms.ModelForm):
    # Use Model's choices directly
    HOUSE_TYPE_CHOICES = Property.HOUSE_TYPE_CHOICES
    GENDER_PREFERENCE_CHOICES = Property.GENDER_PREFERENCE_CHOICES

    # Widgets and labels for better presentation
    title = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Cozy 3-Bedroom Apartment'}),
        label="Property Title"
    )
    house_type = forms.ChoiceField(
        choices=HOUSE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Property Type"
    )
    rent = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 1200.00'}),
        label="Monthly Rent (RM)"
    )
    university_nearby = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., UniKL MIIT, UTM'}),
        label="Nearest University/College"
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Full property address'}),
        label="Full Address"
    )
    bedrooms = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3'}),
        label="Number of Bedrooms"
    )
    total_room = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 5'}),
        label="Total Rooms (incl. living, kitchen etc.)"
    )
    total_toilets = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 2'}),
        label="Total Toilets/Bathrooms"
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Provide a detailed description of your property, amenities, and rules.'}),
        label="Description"
    )
    square_footage = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 950'}),
        label="Square Footage (sq ft)"
    )
    main_image = forms.ImageField(
        required=True, # Make image upload required for new properties
        label="Main Property Image"
    )
    max_tenants = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 4'}),
        label="Maximum Tenants Allowed"
    )
    gender_preferred = forms.ChoiceField(
        choices=GENDER_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tenant Gender Preference"
    )
    # Amenities will be handled by ManyToManyField, which Django's ModelForm renders as a MultipleSelect widget
    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple, # Or forms.SelectMultiple
        required=False,
        label="Amenities"
    )

    class Meta:
        model = Property
        # Include all fields that should be editable by the owner
        fields = [
            'title', 'house_type', 'rent', 'university_nearby', 'address',
            'bedrooms', 'total_room', 'total_toilets', 'description',
            'square_footage', 'main_image', 'max_tenants', 'gender_preferred', 'amenities'
        ]
        # owner and is_available will be set in the view

# --- NEW MODEL: PaymentRecord ---
class PaymentRecord(models.Model):
    id = models.AutoField(primary_key=True)
    # Link to the user who made the payment (optional if anonymous payments are allowed)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_records')
    # If the payment is for a specific booking, link it
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_records')
    # NEW FIELD: Who received the payment (e.g., the owner of the property for a booking)
    receiver_of_payment = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_payments', help_text="The user who is the ultimate recipient of this payment (e.g., owner).")

    full_name = models.CharField(max_length=100, help_text="Full name of the person making the payment.")
    email = models.EmailField(max_length=100, help_text="Email address of the person making the payment.")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number of the person making the payment.")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid.")
    payment_date = models.DateTimeField(default=timezone.now, help_text="Date and time the payment was recorded.")
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True, help_text="Unique transaction ID from payment gateway.")
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Credit Card, Bank Transfer, Online Wallet.")

    class Meta:
        verbose_name_plural = "Payment Records"
        ordering = ['-payment_date'] # Order by most recent payment

    def __str__(self):
        return f"Payment of RM{self.amount} by {self.full_name} on {self.payment_date.strftime('%Y-%m-%d')}"
    
