from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem."""
    model = OrderItem
    extra = 0
    fields = ['product', 'product_name', 'quantity', 'unit', 'unit_price', 'total_price']
    readonly_fields = ['product_name', 'total_price']
    autocomplete_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""
    
    list_display = [
        'order_id_short', 'consumer', 'supplier', 'status_display', 
        'total_amount_display', 'items_count', 'requested_delivery_date', 'created_at'
    ]
    list_filter = ['status', 'supplier', 'created_at', 'requested_delivery_date']
    search_fields = [
        'id', 'consumer__business_name', 'consumer__user__username', 
        'consumer__user__email', 'supplier__name', 'delivery_address', 'notes'
    ]
    autocomplete_fields = ['consumer', 'supplier']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_amount']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'consumer', 'supplier', 'status')
        }),
        ('Financials', {
            'fields': ('total_amount',)
        }),
        ('Logistics', {
            'fields': ('requested_delivery_date', 'delivery_address', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_id_short(self, obj):
        """Display shortened order ID."""
        return format_html('<strong>#{}</strong>', str(obj.id)[:8])
    order_id_short.short_description = 'Order ID'
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'PENDING': 'orange',
            'ACCEPTED': 'blue',
            'PROCESSING': 'purple',
            'READY': 'teal',
            'IN_TRANSIT': 'navy',
            'DELIVERED': 'green',
            'COMPLETED': 'darkgreen',
            'REJECTED': 'red',
            'CANCELLED': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def total_amount_display(self, obj):
        """Display total amount formatted."""
        return format_html('<strong>{} KZT</strong>', obj.total_amount)
    total_amount_display.short_description = 'Total Amount'
    
    def items_count(self, obj):
        """Display count of items in order."""
        count = obj.items.count()
        return format_html('<strong>{}</strong>', count)
    items_count.short_description = 'Items'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('consumer', 'consumer__user', 'supplier')
    
    def save_formset(self, request, form, formset, change):
        """Recalculate order total when items are saved."""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        
        # Recalculate total
        if change:
            order = form.instance
            total = sum(item.total_price for item in order.items.all())
            order.total_amount = total
            order.save()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model (standalone view)."""
    
    list_display = [
        'order', 'product', 'product_name', 'quantity', 'unit', 
        'unit_price', 'total_price_display'
    ]
    list_filter = ['unit', 'order__status', 'order__supplier']
    search_fields = [
        'order__id', 'product_name', 'product_sku', 
        'order__consumer__business_name', 'order__supplier__name'
    ]
    autocomplete_fields = ['order', 'product']
    ordering = ['-order__created_at']
    readonly_fields = ['id', 'total_price']
    
    fieldsets = (
        ('Order Item Information', {
            'fields': ('order', 'product', 'product_name', 'product_sku')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'unit', 'unit_price', 'total_price')
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def total_price_display(self, obj):
        """Display total price formatted."""
        return format_html('<strong>{} KZT</strong>', obj.total_price)
    total_price_display.short_description = 'Total Price'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('order', 'order__consumer', 'order__supplier', 'product')

