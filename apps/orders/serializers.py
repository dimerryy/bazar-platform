"""
Serializers for Order models.
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem
from apps.catalog.models import Product
from apps.users.models import SupplierCompany, ConsumerProfile
from apps.network.models import SupplierConsumerLink


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem."""
    
    product_name = serializers.CharField(read_only=True)
    product_sku = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity', 'unit',
            'unit_price', 'total_price'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'total_price']


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items (used in order creation)."""
    
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, min_value=Decimal('0.01'))
    
    def validate_product_id(self, value):
        """Ensure product exists and is active."""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value
    
    def validate(self, attrs):
        """Validate quantity against product minimum order quantity."""
        product = Product.objects.get(id=attrs['product_id'])
        if attrs['quantity'] < product.min_order_quantity:
            raise serializers.ValidationError({
                'quantity': f"Minimum order quantity is {product.min_order_quantity} {product.unit}."
            })
        if attrs['quantity'] > product.stock_quantity:
            raise serializers.ValidationError({
                'quantity': f"Insufficient stock. Available: {product.stock_quantity} {product.unit}."
            })
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order with nested items."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    consumer_name = serializers.CharField(source='consumer.business_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'consumer', 'consumer_name', 'supplier', 'supplier_name', 'status', 'status_display',
            'total_amount', 'requested_delivery_date', 'delivery_address', 'notes',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'consumer_name', 'supplier_name', 'status_display', 'total_amount',
            'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new order."""
    
    supplier_id = serializers.UUIDField(write_only=True, required=True)
    items = OrderItemCreateSerializer(many=True, required=True, min_length=1)
    
    class Meta:
        model = Order
        fields = [
            'supplier_id', 'requested_delivery_date', 'delivery_address', 'notes', 'items'
        ]
    
    def validate_supplier_id(self, value):
        """Ensure supplier exists and consumer is linked."""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'consumer_profile'):
            raise serializers.ValidationError("User must be a consumer.")
        
        try:
            supplier = SupplierCompany.objects.get(id=value)
        except SupplierCompany.DoesNotExist:
            raise serializers.ValidationError("Supplier not found.")
        
        # Check if consumer is linked to supplier
        consumer = request.user.consumer_profile
        link = SupplierConsumerLink.objects.filter(
            supplier=supplier,
            consumer=consumer,
            status=SupplierConsumerLink.Status.ACTIVE
        ).first()
        
        if not link:
            raise serializers.ValidationError("You must be linked to this supplier before placing an order.")
        
        return value
    
    def validate_items(self, value):
        """Ensure all items belong to the same supplier."""
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        
        supplier_id = self.initial_data.get('supplier_id')
        if not supplier_id:
            return value
        
        try:
            supplier = SupplierCompany.objects.get(id=supplier_id)
        except SupplierCompany.DoesNotExist:
            return value
        
        product_ids = [item['product_id'] for item in value]
        products = Product.objects.filter(id__in=product_ids, supplier=supplier)
        
        if products.count() != len(product_ids):
            raise serializers.ValidationError("All products must belong to the selected supplier.")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        consumer = request.user.consumer_profile
        supplier = SupplierCompany.objects.get(id=validated_data.pop('supplier_id'))
        items_data = validated_data.pop('items')
        
        # Create order
        order = Order.objects.create(
            consumer=consumer,
            supplier=supplier,
            **validated_data
        )
        
        # Create order items and calculate total
        total_amount = Decimal('0.00')
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            
            # Use current price (discount_price if available, else price)
            unit_price = product.current_price
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=quantity,
                unit=product.unit,
                unit_price=unit_price
            )
            
            total_amount += order_item.total_price
        
        # Update order total
        order.total_amount = total_amount
        order.save()
        
        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status (accept/reject/update)."""
    
    status = serializers.ChoiceField(choices=Order.Status.choices, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status transitions based on current status."""
        order = self.context.get('order')
        if not order:
            return value
        
        current_status = order.status
        
        # Define allowed transitions
        allowed_transitions = {
            Order.Status.PENDING: [Order.Status.ACCEPTED, Order.Status.REJECTED, Order.Status.CANCELLED],
            Order.Status.ACCEPTED: [Order.Status.PROCESSING, Order.Status.REJECTED, Order.Status.CANCELLED],
            Order.Status.PROCESSING: [Order.Status.READY, Order.Status.CANCELLED],
            Order.Status.READY: [Order.Status.IN_TRANSIT, Order.Status.CANCELLED],
            Order.Status.IN_TRANSIT: [Order.Status.DELIVERED, Order.Status.CANCELLED],
            Order.Status.DELIVERED: [Order.Status.COMPLETED],
            Order.Status.COMPLETED: [],  # Final state
            Order.Status.REJECTED: [],  # Final state
            Order.Status.CANCELLED: [],  # Final state
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}."
            )
        
        return value
    
    def update(self, instance, validated_data):
        """Update order status."""
        instance.status = validated_data['status']
        instance.save()
        return instance

