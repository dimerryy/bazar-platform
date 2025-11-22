from django.contrib import admin
from django.utils.html import format_html

from .models import SupplierConsumerLink


@admin.register(SupplierConsumerLink)
class SupplierConsumerLinkAdmin(admin.ModelAdmin):
    """Admin interface for SupplierConsumerLink model."""
    
    list_display = [
        'supplier', 'consumer', 'status_display', 'reviewed_by', 
        'orders_count', 'incidents_count', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = [
        'supplier__name', 'consumer__business_name', 
        'consumer__user__username', 'consumer__user__email',
        'reviewed_by__username', 'reviewed_by__email'
    ]
    autocomplete_fields = ['supplier', 'consumer', 'reviewed_by']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('supplier', 'consumer', 'status')
        }),
        ('Review Information', {
            'fields': ('reviewed_by',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'PENDING': 'orange',
            'ACTIVE': 'green',
            'REJECTED': 'red',
            'BLOCKED': 'darkred'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def orders_count(self, obj):
        """Display count of orders for this link."""
        count = obj.consumer.orders.filter(supplier=obj.supplier).count()
        return format_html('<strong>{}</strong>', count)
    orders_count.short_description = 'Orders'
    
    def incidents_count(self, obj):
        """Display count of incidents for this link."""
        count = obj.incidents.count()
        if count > 0:
            open_count = obj.incidents.filter(status='OPEN').count()
            if open_count > 0:
                return format_html(
                    '<strong style="color: red;">{} ({} open)</strong>',
                    count, open_count
                )
        return format_html('<strong>{}</strong>', count)
    incidents_count.short_description = 'Incidents'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'consumer', 'consumer__user', 'reviewed_by')

