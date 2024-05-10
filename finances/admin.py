from django.contrib import admin

# Register your models here.
# finances/admin.py
from django.contrib import admin
from .models import Category


class Category_admin(admin.ModelAdmin):
    list_filter =['username','name','type','budget']
    list_display = ['username','name','type','budget']
admin.site.register(Category,Category_admin)
