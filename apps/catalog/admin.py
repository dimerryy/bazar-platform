from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    
    list_display = ['name', 'category_type', 'supplier', 'products_count', 'description_preview']
    list_filter = ['supplier']
    search_fields = ['name', 'description', 'supplier__name']
    ordering = ['name']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'supplier')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def category_type(self, obj):
        """Display whether category is global or custom."""
        if obj.supplier:
            return format_html('<span style="color: orange;">CUSTOM</span>')
        return format_html('<span style="color: green;">GLOBAL</span>')
    category_type.short_description = 'Type'
    
    def products_count(self, obj):
        """Display count of products in this category."""
        count = obj.products.count()
        return format_html('<strong>{}</strong>', count)
    products_count.short_description = 'Products'
    
    def description_preview(self, obj):
        """Display truncated description."""
        if obj.description:
            preview = obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            return format_html('<span>{}</span>', preview)
        return format_html('<em>No description</em>')
    description_preview.short_description = 'Description'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    
    list_display = [
        'name', 'supplier', 'category', 'current_price_display', 'stock_quantity', 
        'unit', 'is_active', 'created_at'
    ]
    list_filter = ['supplier', 'category', 'is_active', 'unit', 'created_at']
    search_fields = ['name', 'sku', 'description', 'supplier__name']
    autocomplete_fields = ['supplier', 'category']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'current_price_display']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'sku', 'image', 'category')
        }),
        ('Ownership', {
            'fields': ('supplier',)
        }),
        ('Pricing & Units', {
            'fields': ('unit', 'price', 'discount_price', 'current_price_display')
        }),
        ('Inventory & Availability', {
            'fields': ('stock_quantity', 'min_order_quantity', 'is_active')
        }),
        ('Logistics', {
            'fields': ('lead_time_days',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_price_display(self, obj):
        """Display current price with discount indicator."""
        if obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through; color: gray;">{} KZT</span><br>'
                '<strong style="color: green;">{} KZT</strong> (Discounted)',
                obj.price, obj.discount_price
            )
        return format_html('<strong>{} KZT</strong>', obj.price)
    current_price_display.short_description = 'Current Price'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'category')

