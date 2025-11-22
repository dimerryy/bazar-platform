"""
Serializers for Support models (Incident and ChatMessage).
"""
from rest_framework import serializers
from .models import Incident, ChatMessage
from apps.network.models import SupplierConsumerLink
from apps.orders.models import Order


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for Incident."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    link_supplier_name = serializers.CharField(source='link.supplier.name', read_only=True)
    link_consumer_name = serializers.CharField(source='link.consumer.business_name', read_only=True)
    order_id_short = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Incident
        fields = [
            'id', 'link', 'link_supplier_name', 'link_consumer_name', 'order', 'order_id_short',
            'title', 'description', 'status', 'status_display', 'priority', 'priority_display',
            'is_escalated', 'resolved_at', 'messages_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'link_supplier_name', 'link_consumer_name', 'order_id_short',
            'status_display', 'priority_display', 'messages_count', 'created_at', 'updated_at'
        ]
    
    def get_order_id_short(self, obj):
        return str(obj.order.id)[:8] if obj.order else None
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class IncidentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new incident (complaint)."""
    
    order_id = serializers.UUIDField(write_only=True, required=True)
    
    class Meta:
        model = Incident
        fields = ['order_id', 'title', 'description', 'priority']
    
    def validate_order_id(self, value):
        """Ensure order exists and belongs to the consumer."""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'consumer_profile'):
            raise serializers.ValidationError("User must be a consumer.")
        
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        
        # Ensure order belongs to the consumer
        if order.consumer != request.user.consumer_profile:
            raise serializers.ValidationError("Order does not belong to you.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        consumer = request.user.consumer_profile
        order_id = validated_data.pop('order_id')
        order = Order.objects.get(id=order_id)
        
        # Get or create the link
        link = SupplierConsumerLink.objects.get(
            supplier=order.supplier,
            consumer=consumer,
            status=SupplierConsumerLink.Status.ACTIVE
        )
        
        # Create incident
        incident = Incident.objects.create(
            link=link,
            order=order,
            **validated_data
        )
        
        return incident


class IncidentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating incident status."""
    
    status = serializers.ChoiceField(choices=Incident.Status.choices, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status transitions."""
        incident = self.context.get('incident')
        if not incident:
            return value
        
        current_status = incident.status
        
        # Define allowed transitions
        allowed_transitions = {
            Incident.Status.OPEN: [Incident.Status.IN_PROGRESS, Incident.Status.CLOSED],
            Incident.Status.IN_PROGRESS: [Incident.Status.RESOLVED, Incident.Status.CLOSED],
            Incident.Status.RESOLVED: [Incident.Status.CLOSED],
            Incident.Status.CLOSED: [],  # Final state
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}."
            )
        
        return value
    
    def update(self, instance, validated_data):
        """Update incident status."""
        from django.utils import timezone
        
        instance.status = validated_data['status']
        
        # Set resolved_at when status becomes RESOLVED
        if instance.status == Incident.Status.RESOLVED and not instance.resolved_at:
            instance.resolved_at = timezone.now()
        
        instance.save()
        return instance


class IncidentEscalationSerializer(serializers.Serializer):
    """Serializer for escalating an incident (Sales Rep → Manager)."""
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Ensure user is Sales Rep and incident is not already escalated."""
        request = self.context.get('request')
        incident = self.context.get('incident')
        
        if not request or not hasattr(request.user, 'supplier_profile'):
            raise serializers.ValidationError("User must be supplier staff.")
        
        role = request.user.supplier_profile.role
        if role != 'SALES_REP':
            raise serializers.ValidationError("Only Sales Representatives can escalate incidents.")
        
        if incident.is_escalated:
            raise serializers.ValidationError("Incident is already escalated.")
        
        return attrs
    
    def escalate(self, incident):
        """Mark incident as escalated."""
        incident.is_escalated = True
        incident.status = Incident.Status.IN_PROGRESS
        incident.save()
        return incident


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage."""
    
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    attachment_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'link', 'sender', 'sender_username', 'sender_email', 'incident',
            'text', 'attachment', 'attachment_url', 'is_audio', 'is_read',
            'created_at'
        ]
        read_only_fields = [
            'id', 'sender_username', 'sender_email', 'attachment_url', 'is_read', 'created_at'
        ]
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
        return None


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new chat message."""
    
    link_id = serializers.UUIDField(write_only=True, required=True)
    incident_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = ChatMessage
        fields = ['link_id', 'incident_id', 'text', 'attachment', 'is_audio']
    
    def validate_link_id(self, value):
        """Ensure link exists and user is part of the relationship."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated.")
        
        try:
            link = SupplierConsumerLink.objects.get(id=value)
        except SupplierConsumerLink.DoesNotExist:
            raise serializers.ValidationError("Link not found.")
        
        # Check if user is part of this relationship
        is_consumer = (hasattr(request.user, 'consumer_profile') and 
                      link.consumer == request.user.consumer_profile)
        is_supplier_staff = (hasattr(request.user, 'supplier_profile') and 
                            link.supplier == request.user.supplier_profile.company)
        
        if not (is_consumer or is_supplier_staff):
            raise serializers.ValidationError("You are not part of this relationship.")
        
        return value
    
    def validate_incident_id(self, value):
        """Ensure incident exists and belongs to the link if provided."""
        if not value:
            return value
        
        link_id = self.initial_data.get('link_id')
        if not link_id:
            return value
        
        try:
            link = SupplierConsumerLink.objects.get(id=link_id)
            incident = Incident.objects.get(id=value, link=link)
        except (SupplierConsumerLink.DoesNotExist, Incident.DoesNotExist):
            raise serializers.ValidationError("Incident not found or does not belong to this link.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        link_id = validated_data.pop('link_id')
        incident_id = validated_data.pop('incident_id', None)
        
        link = SupplierConsumerLink.objects.get(id=link_id)
        incident = Incident.objects.get(id=incident_id) if incident_id else None
        
        message = ChatMessage.objects.create(
            link=link,
            sender=request.user,
            incident=incident,
            **validated_data
        )
        
        return message


class ChatMessageReadUpdateSerializer(serializers.Serializer):
    """Serializer for marking messages as read."""
    
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    
    def validate_message_ids(self, value):
        """Ensure all messages exist and belong to the user's relationships."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated.")
        
        # Get user's links
        if hasattr(request.user, 'consumer_profile'):
            links = SupplierConsumerLink.objects.filter(consumer=request.user.consumer_profile)
        elif hasattr(request.user, 'supplier_profile'):
            links = SupplierConsumerLink.objects.filter(supplier=request.user.supplier_profile.company)
        else:
            raise serializers.ValidationError("User must be a consumer or supplier staff.")
        
        link_ids = list(links.values_list('id', flat=True))
        
        # Check if all messages belong to user's links
        messages = ChatMessage.objects.filter(id__in=value, link_id__in=link_ids)
        if messages.count() != len(value):
            raise serializers.ValidationError("Some messages not found or not accessible.")
        
        return value
    
    def mark_as_read(self):
        """Mark messages as read."""
        message_ids = self.validated_data['message_ids']
        ChatMessage.objects.filter(id__in=message_ids).update(is_read=True)

