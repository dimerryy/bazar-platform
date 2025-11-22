import uuid

from django.db import models

from apps.users.models import SupplierCompany


class Category(models.Model):
    """
    Product Categories (e.g., 'Dairy', 'Meat', 'Beverages').
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
        KG = 'KG', ('Kilogram')
        LITER = 'L', ('Liter')
        PIECE = 'PCS', ('Piece')
        BOX = 'BOX', ('Box/Crate')
        PACK = 'PACK', ('Pack')
        GRAM = 'G', ('Gram')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    supplier = models.ForeignKey(
        SupplierCompany,
        on_delete=models.CASCADE,
        related_name='products'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(
        max_length=50,
        blank=True,
        help_text="Stock Keeping Unit (Internal Code)"
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)

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