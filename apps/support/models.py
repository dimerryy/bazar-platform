import uuid
from django.db import models
from django.conf import settings
from apps.network.models import SupplierConsumerLink
from apps.orders.models import Order


class Incident(models.Model):
    """
    Represents a formal complaint or issue raised by a Consumer regarding an Order.
    This drives the 'Escalation' workflow.
    """

    class Status(models.TextChoices):
        OPEN = 'OPEN', ('Open')
        IN_PROGRESS = 'IN_PROGRESS', ('In Progress')
        RESOLVED = 'RESOLVED', ('Resolved')
        CLOSED = 'CLOSED', ('Closed')

    class Priority(models.TextChoices):
        LOW = 'LOW', ('Low')
        MEDIUM = 'MEDIUM', ('Medium')
        HIGH = 'HIGH', ('High')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    link = models.ForeignKey(
        SupplierConsumerLink,
        on_delete=models.CASCADE,
        related_name='incidents',
        help_text="The relationship context for this incident."
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='incidents',
        help_text="The specific order this complaint is about."
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    is_escalated = models.BooleanField(
        default=False,
        help_text="If True, requires Manager/Owner attention. Sales Reps can no longer resolve."
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Incident #{str(self.id)[:8]} - {self.title}"


class ChatMessage(models.Model):
    """
    A single message in the communication stream.
    Can be part of a general chat OR tied to a specific Incident.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    link = models.ForeignKey(
        SupplierConsumerLink,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Ensures message stays within the valid B2B relationship."
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_messages'
    )

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )

    text = models.TextField(blank=True, help_text="Text content of the message")
    attachment = models.FileField(
        upload_to='chat_attachments/',
        null=True,
        blank=True,
        help_text="Images, PDFs, or Audio files"
    )
    is_audio = models.BooleanField(default=False, help_text="Frontend flag to render audio player")

    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
