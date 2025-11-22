from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, SupplierCompany, SupplierStaffProfile, ConsumerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ['username', 'email', 'user_type', 'phone_number', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Platform Info', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']


@admin.register(SupplierCompany)
class SupplierCompanyAdmin(admin.ModelAdmin):
    """Admin interface for SupplierCompany model."""
    
    list_display = ['name', 'tax_id', 'is_verified', 'staff_count', 'products_count', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['name', 'tax_id', 'address']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'id']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'tax_id', 'address')
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def staff_count(self, obj):
        """Display count of staff members."""
        count = obj.staff.count()
        return format_html('<strong>{}</strong>', count)
    staff_count.short_description = 'Staff Members'
    
    def products_count(self, obj):
        """Display count of products."""
        count = obj.products.count()
        return format_html('<strong>{}</strong>', count)
    products_count.short_description = 'Products'


class SupplierStaffProfileInline(admin.TabularInline):
    """Inline admin for SupplierStaffProfile."""
    model = SupplierStaffProfile
    extra = 0
    fields = ['user', 'role']
    autocomplete_fields = ['user']


@admin.register(SupplierStaffProfile)
class SupplierStaffProfileAdmin(admin.ModelAdmin):
    """Admin interface for SupplierStaffProfile model."""
    
    list_display = ['user', 'company', 'role', 'user_email', 'user_phone']
    list_filter = ['role', 'company']
    search_fields = ['user__username', 'user__email', 'company__name']
    autocomplete_fields = ['user', 'company']
    ordering = ['company', 'role']
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('user', 'company', 'role')
        }),
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_phone(self, obj):
        """Display user phone."""
        return obj.user.phone_number or '-'
    user_phone.short_description = 'Phone'


@admin.register(ConsumerProfile)
class ConsumerProfileAdmin(admin.ModelAdmin):
    """Admin interface for ConsumerProfile model."""
    
    list_display = ['business_name', 'user', 'contact_person_name', 'user_email', 'user_phone', 'links_count']
    list_filter = ['created_at']
    search_fields = ['business_name', 'user__username', 'user__email', 'contact_person_name', 'address']
    autocomplete_fields = ['user']
    ordering = ['business_name']
    
    fieldsets = (
        ('Business Information', {
            'fields': ('user', 'business_name', 'contact_person_name', 'address')
        }),
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_phone(self, obj):
        """Display user phone."""
        return obj.user.phone_number or '-'
    user_phone.short_description = 'Phone'
    
    def links_count(self, obj):
        """Display count of supplier links."""
        count = obj.supplier_links.count()
        return format_html('<strong>{}</strong>', count)
    links_count.short_description = 'Supplier Links'

