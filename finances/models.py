from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
import uuid

class Account(models.Model):
    """
    Financial account model (bank accounts, credit cards, etc.)
    """
    ACCOUNT_TYPES = [
        ('checking', 'Checking Account'),
        ('savings', 'Savings Account'),
        ('credit_card', 'Credit Card'),
        ('investment', 'Investment Account'),
        ('loan', 'Loan Account'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    institution = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"
    
    def update_balance(self, amount):
        """
        Update account balance with transaction amount
        """
        self.balance += amount
        self.save()

class Category(models.Model):
    """
    Transaction category model
    """
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#000000')
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    """
    Financial transaction model
    """
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    description = models.CharField(max_length=200)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    is_recurring = models.BooleanField(default=False)
    recurring_id = models.UUIDField(null=True, blank=True)
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """
        Update account balance when transaction is saved
        """
        if self.status == 'completed':
            if self.transaction_type == 'income':
                self.account.update_balance(self.amount)
            elif self.transaction_type == 'expense':
                self.account.update_balance(-self.amount)
        super().save(*args, **kwargs)

class RecurringTransaction(models.Model):
    """
    Model for recurring transactions
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='recurring_transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='recurring_transactions')
    transaction_type = models.CharField(max_length=20, choices=Transaction.TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    description = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    last_processed = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('recurring transaction')
        verbose_name_plural = _('recurring transactions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency} ({self.frequency})"

class Budget(models.Model):
    """
    Budget model for tracking spending limits
    """
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('budget')
        verbose_name_plural = _('budgets')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.category.name} - {self.amount} {self.currency} ({self.period})"
    
    def get_spent_amount(self, start_date, end_date):
        """
        Calculate amount spent within date range
        """
        return Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__range=[start_date, end_date]
        ).aggregate(total=models.Sum('amount'))['total'] or 0