from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20) 
    budget = models.DecimalField(max_digits=10, decimal_places=2)  # 'income' or 'expense'

    def __str__(self):
        return self.name