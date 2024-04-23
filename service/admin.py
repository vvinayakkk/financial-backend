from django.contrib import admin

from .models import Transaction

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'amount', 'recurring', 'term', 'end_date']
    list_filter = ['category', 'recurring', 'term']
    search_fields = ['name', 'category', 'description']

admin.site.register(Transaction,TransactionAdmin)
# Register your models here.

