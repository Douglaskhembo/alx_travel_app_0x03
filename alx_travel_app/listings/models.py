from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ------------------------
# Custom User Manager
# ------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, role='GUEST', **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)

        # Automatically assign flags based on role
        if role == 'ADMIN':
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
        elif role == 'HOST':
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', False)
        else:  # GUEST
            extra_fields.setdefault('is_staff', False)
            extra_fields.setdefault('is_superuser', False)

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        return self.create_user(
            email,
            first_name,
            last_name,
            password,
            role='ADMIN',
            **extra_fields
        )

# ------------------------
# Custom User Model
# ------------------------
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('HOST', 'Host'),
        ('GUEST', 'Guest'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='GUEST')
    creation_date = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

# ------------------------
# Listing Model
# ------------------------
class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=100)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ------------------------
# Booking Model
# ------------------------
class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.listing.title}"

# ------------------------
# Review Model
# ------------------------
class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Review for {self.listing.title}"

# ------------------------
# Payment Model
# ------------------------
class Payment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    chapa_tx_ref = models.CharField(max_length=255, unique=True)
    chapa_checkout_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    chapa_tx_id = models.CharField(max_length=255, blank=True, null=True)
    response_log = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment for Booking #{self.booking.id} - {self.status}"
