from django.db import models

# Create your models here.
from django.db import models
from django.db.models import Count


class Transaction(models.Model):
    type = models.CharField(max_length=20,null = True)
    name = models.CharField(max_length=100, blank=True,null=True)
    category = models.CharField(max_length=100,null=True)
    description = models.CharField(max_length=255,null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null = True)  # Set a default value of 0
    recurring = models.BooleanField(default=False, null=True)  # Allow null values
    term = models.CharField(max_length=20,null=True)
    end_date = models.DateField(null = True)

    
# Create your models here.