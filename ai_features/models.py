from django.db import models
from django.conf import settings
from finances.models import Transaction, Category, Account
import uuid
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

class BillUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='bills/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    extracted_data = models.JSONField(null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)  # Store document embeddings
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"{self.user.username}'s bill from {self.uploaded_at}"

class StockNews(models.Model):
    symbol = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    content = models.TextField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    sentiment_score = models.FloatField()
    impact_score = models.FloatField()
    embedding = models.JSONField(null=True, blank=True)  # Store news embeddings
    key_points = ArrayField(models.CharField(max_length=200), default=list)
    market_implications = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.symbol} - {self.title}"

class AIRecommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('investment', 'Investment'),
        ('budget', 'Budget'),
        ('savings', 'Savings'),
        ('risk', 'Risk'),
        ('general', 'General')
    ]
    
    PRIORITY_LEVELS = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    confidence_score = models.FloatField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    context_data = models.JSONField()
    embedding = models.JSONField(null=True, blank=True)  # Store recommendation embeddings
    action_items = ArrayField(models.CharField(max_length=200), default=list)
    expected_impact = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class FinancialInsight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    insight_type = models.CharField(max_length=50)
    data_points = models.JSONField()
    embedding = models.JSONField(null=True, blank=True)  # Store insight embeddings
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class StockPortfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    shares = models.IntegerField()
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    profit_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'symbol']
    
    def __str__(self):
        return f"{self.user.username} - {self.symbol}"

class MarketAnalysis(models.Model):
    symbol = models.CharField(max_length=10)
    analysis_date = models.DateField()
    technical_indicators = models.JSONField()
    fundamental_metrics = models.JSONField()
    ai_prediction = models.JSONField()
    embedding = models.JSONField(null=True, blank=True)  # Store analysis embeddings
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-analysis_date']
        verbose_name_plural = 'Market Analyses'
    
    def __str__(self):
        return f"{self.symbol} - {self.analysis_date}" 