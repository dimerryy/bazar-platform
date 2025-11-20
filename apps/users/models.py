import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom manager to handle email as the unique identifier instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Core User model.
    Differentiates between high-level types (Supplier/Consumer) via 'user_type'.
    Specific business logic resides in the related profiles.
    """

    class UserTypes(models.TextChoices):
        ADMIN = 'ADMIN', _('Platform Admin')
        SUPPLIER = 'SUPPLIER', _('Supplier Staff')
        CONSUMER = 'CONSUMER', _('Consumer (Restaurant/Hotel)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)

    # Core Identity
    user_type = models.CharField(
        max_length=20,
        choices=UserTypes.choices,
        default=UserTypes.CONSUMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default

    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"


# ---------------------------------------------------------
# SUPPLIER DOMAIN
# ---------------------------------------------------------

class SupplierCompany(models.Model):
    """
    Represents the Business Entity (The 'Producer' or 'Distributor').
    Multiple Users (Staff) can belong to one SupplierCompany.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="BIN/IIN or Tax ID")
    address = models.TextField(blank=True)

    # KYB / Verification Status (Managed by Platform Admin)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Supplier Companies"

    def __str__(self):
        return self.name


class SupplierStaffProfile(models.Model):
    """
    Links a User to a SupplierCompany and defines their specific permissions.
    """

    class Roles(models.TextChoices):
        OWNER = 'OWNER', _('Owner')  # Full control
        MANAGER = 'MANAGER', _('Manager')  # Catalog/Orders
        SALES_REP = 'SALES_REP', _('Sales Representative')  # Chat/Ordering

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='supplier_profile'
    )
    company = models.ForeignKey(
        SupplierCompany,
        on_delete=models.CASCADE,
        related_name='staff'
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.SALES_REP
    )

    def __str__(self):
        return f"{self.user.email} - {self.role} at {self.company.name}"


# ---------------------------------------------------------
# CONSUMER DOMAIN
# ---------------------------------------------------------

class ConsumerProfile(models.Model):
    """
    Represents the Restaurant or Hotel.
    In MVP, usually 1 User = 1 Consumer Profile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='consumer_profile'
    )
    business_name = models.CharField(max_length=255, help_text="Name of Restaurant/Hotel")
    address = models.TextField()
    contact_person_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"
