from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
import datetime

class User(AbstractUser):
    objects = CustomUserManager()
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    contact = models.CharField(max_length=10, unique=True,default='')
    dob = models.DateField(default=datetime.date.today)
    monthlyIncome = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gender = models.CharField(max_length=10,default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['contact', 'dob', 'monthlyIncome', 'gender']

     