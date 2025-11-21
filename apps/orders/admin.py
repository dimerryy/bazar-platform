from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # Shows one empty row by default
    readonly_fields = ('total_price',) # Auto-calculated, so don't edit manually
    fields = ('product', 'product_name', 'quantity', 'unit', 'unit_price', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'consumer', 'supplier', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', 'supplier')
    search_fields = ('id', 'consumer__business_name', 'supplier__name')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount',) # Should be calculated from items