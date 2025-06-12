from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    """
    Custom user model with additional fields for financial tracking
    """
    # Personal Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    # Financial Information
    currency = models.CharField(max_length=3, default='USD')
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_score = models.IntegerField(null=True, blank=True)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict)
    theme_preference = models.CharField(max_length=20, default='light')
    language_preference = models.CharField(max_length=10, default='en')
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(auto_now=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Verification
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, null=True, blank=True)
    
    # Social
    social_links = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def is_account_locked(self):
        return self.account_locked_until is not None and self.account_locked_until > timezone.now()
    
    def increment_failed_login_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def reset_failed_login_attempts(self):
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()

class UserProfile(models.Model):
    """
    Extended user profile with additional financial information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Financial Goals
    savings_goal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    investment_goal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    debt_payoff_goal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Risk Profile
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('conservative', 'Conservative'),
            ('moderate', 'Moderate'),
            ('aggressive', 'Aggressive')
        ],
        default='moderate'
    )
    
    # Investment Preferences
    investment_preferences = models.JSONField(default=dict)
    excluded_investments = models.JSONField(default=list)
    
    # Budget Preferences
    budget_categories = models.JSONField(default=dict)
    recurring_expenses = models.JSONField(default=list)
    
    # Analytics Preferences
    analytics_dashboard = models.JSONField(default=dict)
    report_preferences = models.JSONField(default=dict)
    
    # Integration Settings
    connected_accounts = models.JSONField(default=dict)
    api_keys = models.JSONField(default=dict)
    
    # Chatbot Preferences
    chatbot_personality = models.CharField(max_length=50, default='professional')
    chatbot_memory = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def get_risk_score(self):
        """
        Calculate user's risk score based on various factors
        """
        # Implementation of risk score calculation
        pass
    
    def get_investment_recommendations(self):
        """
        Get personalized investment recommendations based on profile
        """
        # Implementation of investment recommendations
        pass
    
    def get_budget_recommendations(self):
        """
        Get personalized budget recommendations based on spending patterns
        """
        # Implementation of budget recommendations
        pass

class UserSession(models.Model):
    """
    Track user sessions and activity
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
    
    def __str__(self):
        return f"{self.user.email} - {self.last_activity}"
    
    def is_expired(self):
        """
        Check if session has expired
        """
        return (timezone.now() - self.last_activity) > timedelta(hours=24)

     