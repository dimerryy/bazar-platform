import uuid

from django.db import models

from apps.catalog.models import Product
from apps.users.models import ConsumerProfile, SupplierCompany


class Order(models.Model):
    """
    Represents a purchase order from a Consumer to a Supplier.
    Orders are always strictly between ONE Consumer and ONE Supplier.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', ('Pending Approval')
        ACCEPTED = 'ACCEPTED', ('Accepted')
        PROCESSING = 'PROCESSING', ('Processing')
        READY = 'READY', ('Ready for Pickup/Delivery')
        IN_TRANSIT = 'IN_TRANSIT', ('In Transit')
        DELIVERED = 'DELIVERED', ('Delivered')
        COMPLETED = 'COMPLETED', ('Completed')
        REJECTED = 'REJECTED', ('Rejected')
        CANCELLED = 'CANCELLED', ('Cancelled')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    consumer = models.ForeignKey(
        ConsumerProfile,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    supplier = models.ForeignKey(
        SupplierCompany,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    requested_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the consumer wants the goods."
    )
    delivery_address = models.TextField(
        help_text="Snapshot of address at time of order"
    )
    notes = models.TextField(blank=True, help_text="Special instructions for Supplier")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['consumer', 'status']),
        ]

    def __str__(self):
        return f"Order #{str(self.id)[:8]} - {self.consumer.business_name}"


class OrderItem(models.Model):
    """
    Individual lines in an Order.
    Stores a SNAPSHOT of the product data to preserve history 
    even if the original Product is modified or deleted.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )

    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50, blank=True)

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount ordered (e.g., 5.5 kg)"
    )
    unit = models.CharField(max_length=10)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price at the moment of purchase"
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    class Meta:
        unique_together = ('order', 'product')

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} {self.unit} x {self.product_name}"