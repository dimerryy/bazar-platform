from django.contrib import admin
from .models import SupplierConsumerLink

@admin.register(SupplierConsumerLink)
class SupplierConsumerLinkAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'supplier', 'status', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('consumer__business_name', 'supplier__name')
    list_editable = ('status',) # Allows quick approval from the list view