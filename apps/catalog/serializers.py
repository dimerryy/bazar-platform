"""
Serializers for Catalog models (Category and Product).
"""
from rest_framework import serializers
from .models import Category, Product
from apps.users.models import SupplierCompany


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""
    
    products_count = serializers.SerializerMethodField()
    category_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'supplier', 'products_count', 'category_type']
        read_only_fields = ['id', 'products_count', 'category_type']
    
    def get_products_count(self, obj):
        return obj.products.count()
    
    def get_category_type(self, obj):
        return 'CUSTOM' if obj.supplier else 'GLOBAL'


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product."""
    
    current_price = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'image', 'category', 'category_name',
            'supplier', 'supplier_name', 'unit', 'price', 'discount_price', 'current_price',
            'stock_quantity', 'min_order_quantity', 'is_active', 'lead_time_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_price', 'supplier_name', 'category_name', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Ensure product belongs to the supplier company of the requesting user."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'supplier_profile'):
            # If creating/updating, ensure supplier matches user's company
            supplier = attrs.get('supplier') or (self.instance.supplier if self.instance else None)
            if supplier and supplier != request.user.supplier_profile.company:
                raise serializers.ValidationError("You can only manage products for your own company.")
        return attrs


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists (optimized for catalog browsing)."""
    
    current_price = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'image_url', 'category_name',
            'supplier_name', 'unit', 'current_price', 'stock_quantity',
            'min_order_quantity', 'is_active', 'lead_time_days'
        ]
        read_only_fields = ['id', 'current_price', 'supplier_name', 'category_name', 'image_url']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

