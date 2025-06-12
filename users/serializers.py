from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, UserSession

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 
                 'phone_number', 'date_of_birth', 'currency', 'monthly_income')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'required': True},
            'date_of_birth': {'required': True},
            'currency': {'required': True},
            'monthly_income': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError('User not found.')
        if not user.check_password(attrs['password']):
            user.increment_failed_login_attempts()
            raise serializers.ValidationError('Invalid credentials.')
        if user.is_account_locked():
            raise serializers.ValidationError('Account is locked. Please try again later.')
        user.reset_failed_login_attempts()
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('savings_goal', 'investment_goal', 'debt_payoff_goal',
                 'risk_tolerance', 'investment_preferences', 'excluded_investments',
                 'budget_categories', 'recurring_expenses', 'analytics_dashboard',
                 'report_preferences', 'connected_accounts', 'api_keys',
                 'chatbot_personality', 'chatbot_memory')

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number',
                 'date_of_birth', 'profile_picture', 'currency', 'monthly_income',
                 'credit_score', 'notification_preferences', 'theme_preference',
                 'language_preference', 'two_factor_enabled', 'email_verified',
                 'phone_verified', 'social_links', 'created_at', 'updated_at',
                 'profile')
        read_only_fields = ('id', 'created_at', 'updated_at', 'email_verified',
                           'phone_verified')

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

class TwoFactorSetupSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    
    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required for 2FA setup.")
        return value

class TwoFactorVerifySerializer(serializers.Serializer):
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Verification code must contain only digits.")
        return value

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ('session_key', 'ip_address', 'user_agent', 'last_activity', 'is_active')
        read_only_fields = ('session_key', 'ip_address', 'user_agent', 'last_activity', 'is_active')

class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)
    
    def validate_provider(self, value):
        allowed_providers = ['google', 'facebook', 'apple', 'linkedin']
        if value not in allowed_providers:
            raise serializers.ValidationError(f"Provider must be one of {allowed_providers}")
        return value

