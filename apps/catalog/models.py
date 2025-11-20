import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import SupplierCompany


class Category(models.Model):
    """
    Product Categories (e.g., 'Dairy', 'Meat', 'Beverages').

    Design Decision:
    - If 'supplier' is NULL, it is a Global Category (managed by Platform Admin).
    - If 'supplier' is SET, it is a custom category created by that Supplier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    supplier = models.ForeignKey(
        SupplierCompany,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True,
        help_text="Null for system-wide categories. Set for supplier-specific categories."
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # # Hierarchy (Optional for MVP, but good for structure)
    # parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        prefix = "GLOBAL" if not self.supplier else "CUSTOM"
        return f"[{prefix}] {self.name}"


class Product(models.Model):
    """
    The core item being sold. 
    Strictly belongs to a SupplierCompany.
    """

    class UnitTypes(models.TextChoices):
        KG = 'KG', _('Kilogram')
        LITER = 'L', _('Liter')
        PIECE = 'PCS', _('Piece')
        BOX = 'BOX', _('Box/Crate')
        PACK = 'PACK', _('Pack')
        GRAM = 'G', _('Gram')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Ownership
    supplier = models.ForeignKey(
        SupplierCompany,
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Organization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    # Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(
        max_length=50,
        blank=True,
        help_text="Stock Keeping Unit (Internal Code)"
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Pricing & Units
    unit = models.CharField(
        max_length=10,
        choices=UnitTypes.choices,
        default=UnitTypes.PIECE
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per Unit in KZT"
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional discounted price"
    )

    # Inventory & Availability
    stock_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    min_order_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text="Minimum amount a consumer must buy"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If False, hidden from catalog but kept for history."
    )

    # Logistics
    lead_time_days = models.PositiveIntegerField(
        default=1,
        help_text="Days required to prepare/ship this item."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier', 'is_active']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price