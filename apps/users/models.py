import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Core User model.
    Differentiates between high-level types (Supplier/Consumer) via 'user_type'.
    Specific business logic resides in the related profiles.
    """

    class UserTypes(models.TextChoices):
        ADMIN = 'ADMIN', ('Platform Admin')
        SUPPLIER = 'SUPPLIER', ('Supplier Staff')
        CONSUMER = 'CONSUMER', ('Consumer (Restaurant/Hotel)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(('email address'))

    user_type = models.CharField(
        max_length=20,
        choices=UserTypes.choices,
        default=UserTypes.CONSUMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


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

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Supplier Companies"

    def __str__(self):
        return self.name


class SupplierStaffProfile(models.Model):
    """
    Links a User to a SupplierCompany and defines their specific permissions.
    """

    class Roles(models.TextChoices):
        OWNER = 'OWNER', ('Owner')
        MANAGER = 'MANAGER', ('Manager')
        SALES_REP = 'SALES_REP', ('Sales Representative')

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"
