from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Account, Transaction, Category, Budget
from decimal import Decimal
import json

User = get_user_model()

class FinancesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test categories
        self.income_category = Category.objects.create(
            user=self.user,
            name='Salary',
            type='income'
        )
        self.expense_category = Category.objects.create(
            user=self.user,
            name='Groceries',
            type='expense'
        )
        
        # Create test account
        self.account = Account.objects.create(
            user=self.user,
            name='Test Bank',
            type='checking',
            balance=Decimal('1000.00')
        )
        
        # Create test budget
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal('500.00'),
            period='monthly'
        )

    def test_account_creation(self):
        """Test creating a new account"""
        url = reverse('account-list')
        data = {
            'name': 'New Account',
            'type': 'savings',
            'balance': '2000.00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 2)

    def test_account_list(self):
        """Test listing accounts"""
        url = reverse('account-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_account_detail(self):
        """Test getting account details"""
        url = reverse('account-detail', args=[self.account.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Bank')

    def test_transaction_creation(self):
        """Test creating a new transaction"""
        url = reverse('transaction-list')
        data = {
            'account': self.account.id,
            'category': self.expense_category.id,
            'amount': '50.00',
            'type': 'expense',
            'description': 'Test transaction'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_transaction_list(self):
        """Test listing transactions"""
        # Create a test transaction
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.expense_category,
            amount=Decimal('50.00'),
            type='expense',
            description='Test transaction'
        )
        
        url = reverse('transaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_category_creation(self):
        """Test creating a new category"""
        url = reverse('category-list')
        data = {
            'name': 'New Category',
            'type': 'expense'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)

    def test_category_list(self):
        """Test listing categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_budget_creation(self):
        """Test creating a new budget"""
        url = reverse('budget-list')
        data = {
            'category': self.expense_category.id,
            'amount': '300.00',
            'period': 'monthly'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Budget.objects.count(), 2)

    def test_budget_list(self):
        """Test listing budgets"""
        url = reverse('budget-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_transaction_summary(self):
        """Test getting transaction summary"""
        # Create test transactions
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.income_category,
            amount=Decimal('1000.00'),
            type='income',
            description='Salary'
        )
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.expense_category,
            amount=Decimal('50.00'),
            type='expense',
            description='Groceries'
        )
        
        url = reverse('transaction-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_income'], '1000.00')
        self.assertEqual(response.data['total_expenses'], '50.00')
        self.assertEqual(response.data['net_amount'], '950.00')

    def test_budget_summary(self):
        """Test getting budget summary"""
        url = reverse('budget-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'Groceries')
        self.assertEqual(response.data[0]['budget_amount'], '500.00')

    def test_category_tree(self):
        """Test getting category tree"""
        # Create a subcategory
        subcategory = Category.objects.create(
            user=self.user,
            name='Fruits',
            type='expense',
            parent=self.expense_category
        )
        
        url = reverse('category-tree')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # income and expense categories
        self.assertEqual(len(response.data[1]['children']), 1)  # expense category has one child

    def test_account_balance_update(self):
        """Test account balance updates with transactions"""
        # Create a transaction
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.expense_category,
            amount=Decimal('50.00'),
            type='expense',
            description='Test transaction'
        )
        
        # Check if account balance was updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('950.00'))

    def test_budget_alert(self):
        """Test budget alert when exceeding budget"""
        # Create transactions exceeding budget
        for _ in range(6):  # Create 6 transactions of 100 each
            Transaction.objects.create(
                user=self.user,
                account=self.account,
                category=self.expense_category,
                amount=Decimal('100.00'),
                type='expense',
                description='Test transaction'
            )
        
        # Check if budget alert was triggered
        url = reverse('budget-alerts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # One alert for exceeding budget
