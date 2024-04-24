from django.contrib import admin

# Register yofrom django.contrib import admin

from .models import Transaction

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['name','type', 'category', 'amount', 'recurring', 'term', 'end_date']
    list_filter = ['category','type', 'recurring', 'term','end_date']
    search_fields = ['name', 'type','category', 'description']

admin.site.register(Transaction,TransactionAdmin)
# Register your models here.ur models here.
