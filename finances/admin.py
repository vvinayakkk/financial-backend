from django.contrib import admin

# Register your models here.
# finances/admin.py
from django.contrib import admin
from .models import Category

admin.site.register(Category)
