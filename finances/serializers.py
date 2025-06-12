from rest_framework import serializers
from django.utils import timezone
from .models import Account, Category, Transaction, RecurringTransaction, Budget

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'category_type', 'parent', 'icon', 'color',
                 'is_default', 'metadata', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        if attrs.get('parent') and attrs['parent'].category_type != attrs['category_type']:
            raise serializers.ValidationError(
                "Parent category must be of the same type."
            )
        return attrs

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'account_type', 'balance', 'currency',
                 'institution', 'account_number', 'is_active', 'last_sync',
                 'metadata', 'created_at', 'updated_at')
        read_only_fields = ('id', 'balance', 'last_sync', 'created_at', 'updated_at')
    
    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Initial balance cannot be negative."
            )
        return value

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ('id', 'account', 'account_name', 'category', 'category_name',
                 'transaction_type', 'amount', 'currency', 'description',
                 'date', 'status', 'is_recurring', 'recurring_id', 'tags',
                 'metadata', 'receipt', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        if attrs.get('date') and attrs['date'] > timezone.now():
            raise serializers.ValidationError(
                "Transaction date cannot be in the future."
            )
        
        if attrs.get('amount') and attrs['amount'] <= 0:
            raise serializers.ValidationError(
                "Transaction amount must be greater than zero."
            )
        
        if attrs.get('category'):
            if attrs['category'].category_type != attrs['transaction_type']:
                raise serializers.ValidationError(
                    "Category type must match transaction type."
                )
        
        return attrs

class RecurringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTransaction
        fields = ('id', 'account', 'category', 'transaction_type', 'amount',
                 'currency', 'description', 'frequency', 'start_date',
                 'end_date', 'last_processed', 'is_active', 'metadata',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'last_processed', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        if attrs.get('start_date') and attrs['start_date'] < timezone.now().date():
            raise serializers.ValidationError(
                "Start date cannot be in the past."
            )
        
        if attrs.get('end_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        
        if attrs.get('amount') and attrs['amount'] <= 0:
            raise serializers.ValidationError(
                "Transaction amount must be greater than zero."
            )
        
        return attrs

class BudgetSerializer(serializers.ModelSerializer):
    spent_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    percentage_used = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Budget
        fields = ('id', 'category', 'amount', 'currency', 'period',
                 'start_date', 'end_date', 'is_active', 'metadata',
                 'spent_amount', 'remaining_amount', 'percentage_used',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        if attrs.get('start_date') and attrs['start_date'] < timezone.now().date():
            raise serializers.ValidationError(
                "Start date cannot be in the past."
            )
        
        if attrs.get('end_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        
        if attrs.get('amount') and attrs['amount'] <= 0:
            raise serializers.ValidationError(
                "Budget amount must be greater than zero."
            )
        
        return attrs
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        start_date = instance.start_date
        end_date = instance.end_date or timezone.now().date()
        
        spent = instance.get_spent_amount(start_date, end_date)
        data['spent_amount'] = spent
        data['remaining_amount'] = instance.amount - spent
        data['percentage_used'] = (spent / instance.amount * 100) if instance.amount > 0 else 0
        
        return data

class TransactionSummarySerializer(serializers.Serializer):
    """
    Serializer for transaction summary statistics
    """
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = serializers.JSONField()
    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

class AccountSummarySerializer(serializers.Serializer):
    """
    Serializer for account summary statistics
    """
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    account_breakdown = serializers.JSONField()
    last_updated = serializers.DateTimeField()

class BudgetSummarySerializer(serializers.Serializer):
    """
    Serializer for budget summary statistics
    """
    total_budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = serializers.JSONField()
    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField() 