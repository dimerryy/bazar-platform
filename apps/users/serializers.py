"""
Serializers for User, Supplier, and Consumer models.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, SupplierCompany, SupplierStaffProfile, ConsumerProfile


class UserSerializer(serializers.ModelSerializer):
    """Basic User serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'user_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupplierCompanySerializer(serializers.ModelSerializer):
    """Serializer for SupplierCompany."""
    
    class Meta:
        model = SupplierCompany
        fields = ['id', 'name', 'tax_id', 'address', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']


class SupplierStaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for SupplierStaffProfile with nested user and company data."""
    
    user = UserSerializer(read_only=True)
    company = SupplierCompanySerializer(read_only=True)
    company_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = SupplierStaffProfile
        fields = ['id', 'user', 'company', 'company_id', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsumerProfileSerializer(serializers.ModelSerializer):
    """Serializer for ConsumerProfile with nested user data."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConsumerProfile
        fields = ['id', 'user', 'business_name', 'address', 'contact_person_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsumerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Consumer registration."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    business_name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    contact_person_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'phone_number', 
                  'business_name', 'address', 'contact_person_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        business_name = validated_data.pop('business_name')
        address = validated_data.pop('address')
        contact_person_name = validated_data.pop('contact_person_name', '')
        
        user = User.objects.create_user(
            user_type=User.UserTypes.CONSUMER,
            password=password,
            **validated_data
        )
        
        ConsumerProfile.objects.create(
            user=user,
            business_name=business_name,
            address=address,
            contact_person_name=contact_person_name
        )
        
        return user


class SupplierRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Supplier Owner registration (creates company and owner profile)."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(required=True)
    company_tax_id = serializers.CharField(required=False, allow_blank=True)
    company_address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'phone_number',
                  'company_name', 'company_tax_id', 'company_address']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        company_name = validated_data.pop('company_name')
        company_tax_id = validated_data.pop('company_tax_id', '')
        company_address = validated_data.pop('company_address', '')
        
        # Create user
        user = User.objects.create_user(
            user_type=User.UserTypes.SUPPLIER,
            password=password,
            **validated_data
        )
        
        # Create supplier company
        company = SupplierCompany.objects.create(
            name=company_name,
            tax_id=company_tax_id,
            address=company_address
        )
        
        # Create owner profile
        SupplierStaffProfile.objects.create(
            user=user,
            company=company,
            role=SupplierStaffProfile.Roles.OWNER
        )
        
        return user


class SupplierStaffCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new Supplier Staff (Manager or Sales Rep) by Owner/Manager."""
    
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    phone_number = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=SupplierStaffProfile.Roles.choices, required=True)
    
    class Meta:
        model = SupplierStaffProfile
        fields = ['username', 'email', 'password', 'phone_number', 'role']
    
    def validate_role(self, value):
        """Ensure only Manager or Sales Rep can be created (not Owner)."""
        if value == SupplierStaffProfile.Roles.OWNER:
            raise serializers.ValidationError("Cannot create Owner role via this endpoint.")
        return value
    
    def create(self, validated_data):
        # Get company from the requesting user
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'supplier_profile'):
            raise serializers.ValidationError("User must be a supplier staff member.")
        
        company = request.user.supplier_profile.company
        
        # Check permissions - only Owner and Manager can create staff
        role = request.user.supplier_profile.role
        if role not in [SupplierStaffProfile.Roles.OWNER, SupplierStaffProfile.Roles.MANAGER]:
            raise serializers.ValidationError("Only Owner and Manager can create staff members.")
        
        # Check if Manager is trying to create another Manager (not allowed)
        if role == SupplierStaffProfile.Roles.MANAGER:
            if validated_data['role'] == SupplierStaffProfile.Roles.MANAGER:
                raise serializers.ValidationError("Managers cannot create other Managers.")
        
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        phone_number = validated_data.pop('phone_number', '')
        role = validated_data.pop('role')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            user_type=User.UserTypes.SUPPLIER
        )
        
        # Create staff profile
        staff_profile = SupplierStaffProfile.objects.create(
            user=user,
            company=company,
            role=role
        )
        
        return staff_profile

