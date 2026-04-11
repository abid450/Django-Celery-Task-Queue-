from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.conf import settings
from .models import User, EmailVerification, VerificationLog
from .utils import generate_verification_code, mask_email, get_client_ip, get_user_agent

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'phone_number', 'bio', 'profile_picture', 'is_active', 
                  'is_email_verified', 'date_joined', 'last_login', 'email_verified_at']
        read_only_fields = ['id', 'is_active', 'is_email_verified', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone_number']
    
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
    
    def validate(self, data):
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError({"password2": "Password fields didn't match."})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        verification_code = generate_verification_code()
        EmailVerification.objects.create(user=user, verification_code=verification_code)
        
        return user

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    verification_code = serializers.CharField(min_length=6, max_length=10, required=True)
    
    def validate_email(self, value):
        try:
            self.user = User.objects.get(email__iexact=value.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        
        if self.user.is_email_verified:
            raise serializers.ValidationError("Email already verified.")
        
        return value.lower()
    
    def validate(self, data):
        user = getattr(self, 'user', None)
        if not user:
            raise serializers.ValidationError("Invalid email address.")
        
        try:
            verification = EmailVerification.objects.get(user=user, is_used=False)
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("No pending verification found.")
        
        if verification.is_expired():
            raise serializers.ValidationError("Verification code has expired.")
        
        if verification.verification_code != data.get('verification_code'):
            verification.mark_as_failed()
            raise serializers.ValidationError("Invalid verification code.")
        
        data['verification'] = verification
        return data

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        
        if user.is_email_verified:
            raise serializers.ValidationError("Email already verified.")
        
        self.user = user
        return value.lower()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return data

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'bio', 'profile_picture']

class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'first_name', 'last_name',
                  'phone_number', 'bio', 'profile_picture', 'is_email_verified',
                  'is_active', 'date_joined', 'last_login', 'email_verified_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()