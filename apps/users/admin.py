from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SupplierCompany, SupplierStaffProfile, ConsumerProfile
from django.contrib.auth.models import Group

admin.site.unregister(Group)


class SupplierStaffInline(admin.StackedInline):
    model = SupplierStaffProfile
    can_delete = False
    verbose_name_plural = 'Supplier Staff Profile'
    fk_name = 'user'


class ConsumerProfileInline(admin.StackedInline):
    model = ConsumerProfile
    can_delete = False
    verbose_name_plural = 'Consumer Profile'
    fk_name = 'user'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin to handle our custom user model and show profiles inline.
    """
    model = User
    list_display = ('email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions',
         {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('email',)

    # Show the appropriate profile form based on the user type (Dynamic would be JS, strictly showing both for now)
    inlines = [SupplierStaffInline, ConsumerProfileInline]


@admin.register(SupplierCompany)
class SupplierCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('name', 'tax_id')
    actions = ['mark_verified']

    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)

    mark_verified.short_description = "Mark selected companies as Verified (KYB)"