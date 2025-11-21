from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier')
    list_filter = ('supplier',) # Null suppliers = Global Categories
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'category', 'price', 'stock_quantity', 'unit', 'is_active')
    list_filter = ('supplier', 'is_active', 'category')
    search_fields = ('name', 'sku', 'supplier__name')
    list_editable = ('price', 'stock_quantity', 'is_active') # Quick editing