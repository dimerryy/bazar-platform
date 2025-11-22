"""
Serializers for Network models (Supplier-Consumer Links).
"""
from rest_framework import serializers
from .models import SupplierConsumerLink
from apps.users.models import SupplierCompany, ConsumerProfile


class SupplierConsumerLinkSerializer(serializers.ModelSerializer):
    """Serializer for SupplierConsumerLink."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    consumer_name = serializers.CharField(source='consumer.business_name', read_only=True)
    consumer_email = serializers.CharField(source='consumer.user.email', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    orders_count = serializers.SerializerMethodField()
    incidents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SupplierConsumerLink
        fields = [
            'id', 'supplier', 'supplier_name', 'consumer', 'consumer_name', 'consumer_email',
            'status', 'reviewed_by', 'reviewed_by_username', 'orders_count', 'incidents_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'supplier_name', 'consumer_name', 'consumer_email', 'reviewed_by_username',
            'orders_count', 'incidents_count', 'created_at', 'updated_at'
        ]
    
    def get_orders_count(self, obj):
        return obj.consumer.orders.filter(supplier=obj.supplier).count()
    
    def get_incidents_count(self, obj):
        return obj.incidents.count()


class LinkRequestSerializer(serializers.ModelSerializer):
    """Serializer for Consumer to request a link to a Supplier."""
    
    supplier_id = serializers.UUIDField(write_only=True, required=True)
    
    class Meta:
        model = SupplierConsumerLink
        fields = ['supplier_id']
    
    def validate_supplier_id(self, value):
        """Ensure supplier exists."""
        try:
            SupplierCompany.objects.get(id=value)
        except SupplierCompany.DoesNotExist:
            raise serializers.ValidationError("Supplier not found.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'consumer_profile'):
            raise serializers.ValidationError("User must be a consumer.")
        
        supplier_id = validated_data.pop('supplier_id')
        supplier = SupplierCompany.objects.get(id=supplier_id)
        consumer = request.user.consumer_profile
        
        # Check if link already exists
        link, created = SupplierConsumerLink.objects.get_or_create(
            supplier=supplier,
            consumer=consumer,
            defaults={'status': SupplierConsumerLink.Status.PENDING}
        )
        
        if not created:
            if link.status == SupplierConsumerLink.Status.ACTIVE:
                raise serializers.ValidationError("You are already linked to this supplier.")
            elif link.status == SupplierConsumerLink.Status.PENDING:
                raise serializers.ValidationError("Link request is already pending.")
            elif link.status == SupplierConsumerLink.Status.BLOCKED:
                raise serializers.ValidationError("You are blocked from this supplier.")
            else:
                # Reset to pending if previously rejected
                link.status = SupplierConsumerLink.Status.PENDING
                link.save()
        
        return link


class LinkApprovalSerializer(serializers.Serializer):
    """Serializer for Supplier to approve/reject a link request."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject', 'block'], required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'supplier_profile'):
            raise serializers.ValidationError("User must be supplier staff.")
        
        # Check permissions - only Owner and Manager can approve/reject
        role = request.user.supplier_profile.role
        if role not in ['OWNER', 'MANAGER']:
            raise serializers.ValidationError("Only Owner and Manager can approve/reject links.")
        
        return attrs
    
    def update_link(self, link):
        """Update link status based on action."""
        action = self.validated_data['action']
        request = self.context.get('request')
        
        if action == 'approve':
            link.status = SupplierConsumerLink.Status.ACTIVE
        elif action == 'reject':
            link.status = SupplierConsumerLink.Status.REJECTED
        elif action == 'block':
            link.status = SupplierConsumerLink.Status.BLOCKED
        
        link.reviewed_by = request.user
        link.save()
        
        return link

