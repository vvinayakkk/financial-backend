# finances/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet, CategoryViewSet, TransactionViewSet,
    RecurringTransactionViewSet, BudgetViewSet, FinancialReportViewSet
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'recurring', RecurringTransactionViewSet, basename='recurring')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'reports', FinancialReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]