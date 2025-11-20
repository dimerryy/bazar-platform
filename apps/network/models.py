import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import SupplierCompany, ConsumerProfile


class SupplierConsumerLink(models.Model):
    """
    Represents the B2B relationship between a Supplier Company and a Consumer.
    This acts as a permission gate:
    - If Status is NOT 'ACTIVE', Consumer cannot see Catalog.
    - If Status is NOT 'ACTIVE', Consumer cannot create Orders.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        ACTIVE = 'ACTIVE', _('Active')  # The only status that allows trading
        REJECTED = 'REJECTED', _('Rejected')  # Explicit rejection
        BLOCKED = 'BLOCKED', _('Blocked')  # Relationship terminated negatively

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # The two parties involved
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

    # State of the relationship
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tracks which Supplier Manager/Owner approved or blocked this link
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
        # Prevent duplicate requests between the same two entities
        unique_together = ('supplier', 'consumer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.consumer.business_name} -> {self.supplier.name} [{self.status}]"
