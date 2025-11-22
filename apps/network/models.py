import uuid

from django.conf import settings
from django.db import models

from apps.users.models import SupplierCompany, ConsumerProfile


class SupplierConsumerLink(models.Model):
    """
    Represents the B2B relationship between a Supplier Company and a Consumer.
    This acts as a permission gate:
    - If Status is NOT 'ACTIVE', Consumer cannot see Catalog.
    - If Status is NOT 'ACTIVE', Consumer cannot create Orders.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', ('Pending Approval')
        ACTIVE = 'ACTIVE', ('Active')
        REJECTED = 'REJECTED', ('Rejected')
        BLOCKED = 'BLOCKED', ('Blocked')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    supplier = models.ForeignKey(
        SupplierCompany,
        on_delete=models.CASCADE,
        related_name='consumer_links'
    )
    consumer = models.ForeignKey(
        ConsumerProfile,
        on_delete=models.CASCADE,
        related_name='supplier_links'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_links',
        help_text="The Supplier User who approved/rejected this link."
    )

    class Meta:
        verbose_name = "Supplier-Consumer Link"
        verbose_name_plural = "Supplier-Consumer Links"
        unique_together = ('supplier', 'consumer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.consumer.business_name} -> {self.supplier.name} [{self.status}]"
