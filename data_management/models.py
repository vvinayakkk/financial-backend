from django.db import models
from django.contrib.auth import get_user_model
from finances.models import Transaction, Account, Category, Budget

User = get_user_model()

class DataExport(models.Model):
    """Model for tracking data exports"""
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ]
    
    EXPORT_TYPES = [
        ('transactions', 'Transactions'),
        ('accounts', 'Accounts'),
        ('categories', 'Categories'),
        ('budgets', 'Budgets'),
        ('reports', 'Reports'),
        ('all', 'All Data'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPES)
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file = models.FileField(upload_to='exports/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    filters = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.export_type} export ({self.format})"

class DataImport(models.Model):
    """Model for tracking data imports"""
    IMPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    IMPORT_TYPES = [
        ('transactions', 'Transactions'),
        ('accounts', 'Accounts'),
        ('categories', 'Categories'),
        ('budgets', 'Budgets'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    format = models.CharField(max_length=10, choices=IMPORT_FORMATS)
    file = models.FileField(upload_to='imports/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.import_type} import ({self.format})"

class SavedVisualization(models.Model):
    """Model for saving user-created visualizations"""
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('scatter', 'Scatter Plot'),
        ('area', 'Area Chart'),
        ('radar', 'Radar Chart'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES)
    data_source = models.CharField(max_length=50)  # e.g., 'transactions', 'budgets'
    filters = models.JSONField(default=dict)
    configuration = models.JSONField(default=dict)  # Chart configuration
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username}'s {self.name} visualization"

class DataSync(models.Model):
    """Model for tracking data synchronization with external services"""
    SYNC_TYPES = [
        ('bank', 'Bank Account'),
        ('investment', 'Investment Account'),
        ('tax', 'Tax Software'),
        ('accounting', 'Accounting Software'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    service_name = models.CharField(max_length=100)
    last_sync = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    configuration = models.JSONField(default=dict)
    error_log = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-last_sync']
        unique_together = ['user', 'sync_type', 'service_name']
    
    def __str__(self):
        return f"{self.user.username}'s {self.service_name} sync"

class Backup(models.Model):
    """Model for tracking data backups"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='backups/')
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, default='pending')
    type = models.CharField(max_length=20, default='full')  # full or incremental
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s backup ({self.created_at})" 