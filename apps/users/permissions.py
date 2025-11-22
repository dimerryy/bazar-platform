"""
Permission classes for role-based access control in the Supplier Consumer Platform.
"""
from rest_framework import permissions
from apps.users.models import SupplierStaffProfile


class IsSupplierStaff(permissions.BasePermission):
    """
    Permission to check if user is a Supplier Staff (Owner, Manager, or Sales Rep).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'SUPPLIER' and hasattr(request.user, 'supplier_profile')


class IsSupplierOwner(permissions.BasePermission):
    """
    Permission to check if user is a Supplier Owner.
    Owner has full control including creating/removing managers and deleting account.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'SUPPLIER':
            return False
        if not hasattr(request.user, 'supplier_profile'):
            return False
        return request.user.supplier_profile.role == SupplierStaffProfile.Roles.OWNER


class IsSupplierManagerOrOwner(permissions.BasePermission):
    """
    Permission to check if user is a Supplier Manager or Owner.
    Both can handle catalog, inventory, and escalations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'SUPPLIER':
            return False
        if not hasattr(request.user, 'supplier_profile'):
            return False
        role = request.user.supplier_profile.role
        return role in [SupplierStaffProfile.Roles.OWNER, SupplierStaffProfile.Roles.MANAGER]


class IsSupplierSalesRepOrAbove(permissions.BasePermission):
    """
    Permission to check if user is a Sales Rep, Manager, or Owner.
    Sales Reps can handle consumer communication and first-line complaints.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'SUPPLIER':
            return False
        if not hasattr(request.user, 'supplier_profile'):
            return False
        role = request.user.supplier_profile.role
        return role in [
            SupplierStaffProfile.Roles.OWNER,
            SupplierStaffProfile.Roles.MANAGER,
            SupplierStaffProfile.Roles.SALES_REP
        ]


class IsConsumer(permissions.BasePermission):
    """
    Permission to check if user is a Consumer (Restaurant/Hotel).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'CONSUMER' and hasattr(request.user, 'consumer_profile')


class IsSupplierOwnerOrManager(permissions.BasePermission):
    """
    Alias for IsSupplierManagerOrOwner for clarity.
    """
    def has_permission(self, request, view):
        perm = IsSupplierManagerOrOwner()
        return perm.has_permission(request, view)


class IsLinkedConsumer(permissions.BasePermission):
    """
    Permission to check if Consumer is linked (ACTIVE status) to a specific Supplier.
    Used for catalog visibility and order creation.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'CONSUMER':
            return False
        if not hasattr(request.user, 'consumer_profile'):
            return False
        
        # Check if consumer is linked to the supplier
        from apps.network.models import SupplierConsumerLink
        from apps.users.models import SupplierCompany
        
        # If obj is a SupplierCompany, check link directly
        if isinstance(obj, SupplierCompany):
            link = SupplierConsumerLink.objects.filter(
                supplier=obj,
                consumer=request.user.consumer_profile,
                status=SupplierConsumerLink.Status.ACTIVE
            ).first()
            return link is not None
        
        # If obj has a supplier attribute (like Product), check that
        if hasattr(obj, 'supplier'):
            link = SupplierConsumerLink.objects.filter(
                supplier=obj.supplier,
                consumer=request.user.consumer_profile,
                status=SupplierConsumerLink.Status.ACTIVE
            ).first()
            return link is not None
        
        return False


class IsSupplierCompanyMember(permissions.BasePermission):
    """
    Permission to check if Supplier Staff belongs to a specific SupplierCompany.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'SUPPLIER':
            return False
        if not hasattr(request.user, 'supplier_profile'):
            return False
        
        from apps.users.models import SupplierCompany
        
        # If obj is a SupplierCompany, check membership
        if isinstance(obj, SupplierCompany):
            return request.user.supplier_profile.company == obj
        
        # If obj has a supplier attribute, check membership
        if hasattr(obj, 'supplier'):
            return request.user.supplier_profile.company == obj.supplier
        
        return False

