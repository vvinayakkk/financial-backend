from django.shortcuts import render

# Create your views here.
# finances/views.py
import logging
from django.http import JsonResponse
from .models import Category
import json
from django.views.decorators.csrf import csrf_exempt
import jwt
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta, datetime
import calendar
import pandas as pd
import numpy as np
from scipy import stats
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Account, Transaction, RecurringTransaction, Budget
from .serializers import (
    AccountSerializer, CategorySerializer, TransactionSerializer,
    RecurringTransactionSerializer, BudgetSerializer,
    TransactionSummarySerializer, AccountSummarySerializer,
    BudgetSummarySerializer
)

logger = logging.getLogger(__name__)

@csrf_exempt
def add_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            logger.info(f"Received data: {data}")
            authorization_header = request.headers.get('Authorization')
            print("Authorization Header:", authorization_header) 
            decoded_token = jwt.decode(authorization_header,'secret',algorithms=['HS256'])
            print("Decoded Token:", decoded_token)
            username = decoded_token['username']
            
            # Process data and create a new category
            category = Category.objects.create(
                username=username,
                name=data['name'],
                type=data['type'],
                budget=data['budget']
            )
            logger.info(f"Created category: {category}")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception("Error adding category:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)



@csrf_exempt
def delete_category(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        authorization_header = request.headers.get('Authorization')
        decoded_token = jwt.decode(authorization_header,'secret',algorithms=['HS256'])
        user_name = decoded_token['username']

        try:
            category = Category.objects.get(name=data['name'], type=data['type'],username=user_name)
            category.delete()
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    elif request.method == 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def reload_categories(request):
    if request.method == 'GET':
        try:
            authorization_header = request.headers.get('Authorization')
            print(authorization_header)
            decoded_token = jwt.decode(authorization_header,'secret',algorithms=['HS256'])
            user_name = decoded_token['username']
            # Retrieve all categories from the database
            categories = Category.objects.filter(username=user_name)
            logger.info(f"Retrieved categories: {categories}")
            # Convert categories to JSON format
            categories_json = [{'name': category.name, 'type': category.type, 'budget': category.budget,} for category in categories]
            # Return categories as JSON response
            return JsonResponse(categories_json, safe=False)
        except Exception as e:
            logger.exception("Error reloading categories:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def update_budget(request):
    if request.method == 'POST':
        try:
            authorization_header = request.headers.get('Authorization')
            decoded_token = jwt.decode(authorization_header,'secret',algorithms=['HS256'])
            user_name = decoded_token['username']
            data = json.loads(request.body)
            category_name = data.get('category')
            category_type = data.get('type')
            new_budget = data.get('budget')

            category = Category.objects.get(name=category_name, type=category_type,username=user_name)
            category.budget = new_budget
            category.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception("Error updating budget:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_type', 'currency', 'is_active']
    search_fields = ['name', 'institution', 'account_number']
    ordering_fields = ['name', 'balance', 'created_at']
    
    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        accounts = self.get_queryset()
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
        currency = request.user.currency
        
        account_breakdown = []
        for account in accounts:
            account_breakdown.append({
                'id': str(account.id),
                'name': account.name,
                'type': account.account_type,
                'balance': account.balance,
                'currency': account.currency,
                'percentage': (account.balance / total_balance * 100) if total_balance > 0 else 0
            })
        
        data = {
            'total_balance': total_balance,
            'currency': currency,
            'account_breakdown': account_breakdown,
            'last_updated': timezone.now()
        }
        
        serializer = AccountSummarySerializer(data)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_type', 'is_default']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get category hierarchy
        """
        categories = self.get_queryset()
        root_categories = categories.filter(parent=None)
        
        def build_tree(category):
            children = categories.filter(parent=category)
            return {
                'id': str(category.id),
                'name': category.name,
                'type': category.category_type,
                'icon': category.icon,
                'color': category.color,
                'children': [build_tree(child) for child in children]
            }
        
        tree = [build_tree(category) for category in root_categories]
        return Response(tree)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'is_recurring', 'currency']
    search_fields = ['description', 'tags']
    ordering_fields = ['date', 'amount', 'created_at']
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        period = request.query_params.get('period', 'month')
        end_date = timezone.now()
        
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date.replace(day=1)
        elif period == 'year':
            start_date = end_date.replace(month=1, day=1)
        else:
            return Response(
                {'error': 'Invalid period. Use week, month, or year.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transactions = self.get_queryset().filter(date__range=[start_date, end_date])
        
        total_income = transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_expenses = transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        category_breakdown = {}
        for transaction in transactions:
            category = transaction.category.name if transaction.category else 'Uncategorized'
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'income': 0,
                    'expenses': 0
                }
            
            if transaction.transaction_type == 'income':
                category_breakdown[category]['income'] += transaction.amount
            else:
                category_breakdown[category]['expenses'] += transaction.amount
        
        data = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_amount': total_income - total_expenses,
            'category_breakdown': category_breakdown,
            'period': period,
            'start_date': start_date,
            'end_date': end_date
        }
        
        serializer = TransactionSummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Analyze transaction trends over time."""
        user = request.user
        period = request.query_params.get('period', 'monthly')  # weekly, monthly, yearly
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date().isoformat())
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            if period == 'weekly':
                start_date = timezone.now().date() - timedelta(days=30)
            elif period == 'monthly':
                start_date = timezone.now().date() - timedelta(days=365)
            else:  # yearly
                start_date = timezone.now().date() - timedelta(days=365*3)
        
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get transactions for the period
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(list(transactions.values()))
        if df.empty:
            return Response({
                'message': 'No transactions found for the specified period.',
                'trends': {}
            })
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Set date as index
        df.set_index('date', inplace=True)
        
        # Resample based on period
        if period == 'weekly':
            freq = 'W'
        elif period == 'monthly':
            freq = 'M'
        else:  # yearly
            freq = 'Y'
        
        # Calculate trends
        trends = {}
        
        # Income trends
        income_df = df[df['type'] == 'income'].resample(freq)['amount'].sum()
        if not income_df.empty:
            trends['income'] = {
                'data': income_df.to_dict(),
                'stats': {
                    'mean': income_df.mean(),
                    'std': income_df.std(),
                    'trend': self._calculate_trend(income_df),
                    'volatility': self._calculate_volatility(income_df)
                }
            }
        
        # Expense trends
        expense_df = df[df['type'] == 'expense'].resample(freq)['amount'].sum()
        if not expense_df.empty:
            trends['expenses'] = {
                'data': expense_df.to_dict(),
                'stats': {
                    'mean': expense_df.mean(),
                    'std': expense_df.std(),
                    'trend': self._calculate_trend(expense_df),
                    'volatility': self._calculate_volatility(expense_df)
                }
            }
        
        # Category-wise trends
        category_trends = {}
        for category in Category.objects.filter(user=user):
            cat_df = df[df['category_id'] == category.id].resample(freq)['amount'].sum()
            if not cat_df.empty:
                category_trends[category.name] = {
                    'data': cat_df.to_dict(),
                    'stats': {
                        'mean': cat_df.mean(),
                        'std': cat_df.std(),
                        'trend': self._calculate_trend(cat_df),
                        'volatility': self._calculate_volatility(cat_df)
                    }
                }
        trends['categories'] = category_trends
        
        # Savings rate trend
        if not income_df.empty and not expense_df.empty:
            savings_df = (income_df - expense_df) / income_df * 100
            trends['savings_rate'] = {
                'data': savings_df.to_dict(),
                'stats': {
                    'mean': savings_df.mean(),
                    'std': savings_df.std(),
                    'trend': self._calculate_trend(savings_df),
                    'volatility': self._calculate_volatility(savings_df)
                }
            }
        
        # Spending patterns
        if not expense_df.empty:
            # Calculate day of week spending
            df['day_of_week'] = df.index.dayofweek
            day_spending = df[df['type'] == 'expense'].groupby('day_of_week')['amount'].mean()
            trends['day_of_week_spending'] = {
                'data': day_spending.to_dict(),
                'highest_spending_day': day_spending.idxmax(),
                'lowest_spending_day': day_spending.idxmin()
            }
        
        # Anomaly detection
        if not expense_df.empty:
            trends['anomalies'] = self._detect_anomalies(expense_df)
        
        return Response({
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trends': trends
        })
    
    def _calculate_trend(self, series):
        """Calculate the trend direction and strength."""
        if len(series) < 2:
            return 'insufficient_data'
        
        # Calculate linear regression
        x = np.arange(len(series))
        y = series.values
        slope, _, r_value, _, _ = stats.linregress(x, y)
        
        # Determine trend direction and strength
        if abs(r_value) < 0.3:
            return 'no_trend'
        elif slope > 0:
            return 'increasing' if r_value > 0.7 else 'slightly_increasing'
        else:
            return 'decreasing' if r_value < -0.7 else 'slightly_decreasing'
    
    def _calculate_volatility(self, series):
        """Calculate the volatility of the series."""
        if len(series) < 2:
            return 'insufficient_data'
        
        cv = series.std() / series.mean()  # Coefficient of variation
        
        if cv < 0.1:
            return 'low'
        elif cv < 0.3:
            return 'medium'
        else:
            return 'high'
    
    def _detect_anomalies(self, series, threshold=2):
        """Detect anomalies using z-score method."""
        if len(series) < 3:
            return []
        
        z_scores = np.abs(stats.zscore(series))
        anomalies = series[z_scores > threshold]
        
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'value': value,
                'z_score': float(z_scores[series.index.get_loc(date)])
            }
            for date, value in anomalies.items()
        ]

class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'frequency', 'is_active']
    search_fields = ['description']
    ordering_fields = ['start_date', 'amount', 'created_at']
    
    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process a recurring transaction and create a new transaction if due."""
        recurring = self.get_object()
        
        if not recurring.is_active:
            return Response(
                {'error': 'Recurring transaction is not active.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the transaction is due
        if not self._is_due(recurring):
            return Response(
                {'message': 'Transaction is not due yet.'},
                status=status.HTTP_200_OK
            )
        
        # Create the transaction
        try:
            with transaction.atomic():
                new_transaction = Transaction.objects.create(
                    user=request.user,
                    type=recurring.type,
                    amount=recurring.amount,
                    category=recurring.category,
                    account=recurring.account,
                    description=recurring.description,
                    date=timezone.now().date(),
                    status='completed',
                    recurring_transaction=recurring
                )
                
                # Update last processed date
                recurring.last_processed = timezone.now()
                recurring.save()
                
                return Response(
                    TransactionSerializer(new_transaction).data,
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_due(self, recurring):
        """Check if the recurring transaction is due for processing."""
        now = timezone.now()
        
        # If never processed, check if it's past the start date
        if not recurring.last_processed:
            return now.date() >= recurring.start_date
        
        # If end date is reached, not due
        if recurring.end_date and now.date() > recurring.end_date:
            return False
        
        # Calculate next due date based on frequency
        if recurring.frequency == 'daily':
            next_due = recurring.last_processed + timedelta(days=1)
        elif recurring.frequency == 'weekly':
            next_due = recurring.last_processed + timedelta(weeks=1)
        elif recurring.frequency == 'monthly':
            # Handle month boundaries correctly
            if recurring.last_processed.month == 12:
                next_due = recurring.last_processed.replace(year=recurring.last_processed.year + 1, month=1)
            else:
                next_due = recurring.last_processed.replace(month=recurring.last_processed.month + 1)
        elif recurring.frequency == 'yearly':
            next_due = recurring.last_processed.replace(year=recurring.last_processed.year + 1)
        else:
            return False
        
        return now.date() >= next_due.date()

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get comprehensive budget summary and analysis."""
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date().isoformat())
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date().replace(day=1)  # Start of current month
        
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get all budgets for the period
        budgets = Budget.objects.filter(
            user=user,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # Get all transactions for the period
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date,
            type='expense'
        )
        
        # Calculate overall budget metrics
        total_budget = budgets.aggregate(total=Sum('amount'))['total'] or 0
        total_spent = transactions.aggregate(total=Sum('amount'))['total'] or 0
        remaining = total_budget - total_spent
        
        # Calculate category-wise budget and spending
        category_analysis = {}
        for budget in budgets:
            category = budget.category
            category_transactions = transactions.filter(category=category)
            spent = category_transactions.aggregate(total=Sum('amount'))['total'] or 0
            
            category_analysis[category.name] = {
                'budgeted': budget.amount,
                'spent': spent,
                'remaining': budget.amount - spent,
                'percentage_used': (spent / budget.amount * 100) if budget.amount > 0 else 0,
                'status': self._get_budget_status(spent, budget.amount)
            }
        
        # Calculate spending trends
        daily_spending = transactions.values('date').annotate(
            total=Sum('amount')
        ).order_by('date')
        
        # Calculate budget utilization rate
        utilization_rate = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        # Calculate budget variance
        variance = total_spent - total_budget
        variance_percentage = (variance / total_budget * 100) if total_budget > 0 else 0
        
        # Get top spending categories
        top_categories = transactions.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]
        
        # Calculate budget health score
        health_score = self._calculate_budget_health(
            utilization_rate,
            variance_percentage,
            category_analysis
        )
        
        return Response({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'overall': {
                'total_budget': total_budget,
                'total_spent': total_spent,
                'remaining': remaining,
                'utilization_rate': utilization_rate,
                'variance': variance,
                'variance_percentage': variance_percentage,
                'health_score': health_score
            },
            'categories': category_analysis,
            'top_spending_categories': [
                {
                    'category': item['category__name'],
                    'amount': item['total'],
                    'percentage': (item['total'] / total_spent * 100) if total_spent > 0 else 0
                }
                for item in top_categories
            ],
            'daily_spending': [
                {
                    'date': item['date'].isoformat(),
                    'amount': item['total']
                }
                for item in daily_spending
            ]
        })
    
    def _get_budget_status(self, spent, budgeted):
        """Determine the status of a budget category."""
        if budgeted == 0:
            return 'no_budget'
        
        percentage = (spent / budgeted * 100)
        
        if percentage >= 100:
            return 'exceeded'
        elif percentage >= 90:
            return 'warning'
        elif percentage >= 75:
            return 'caution'
        else:
            return 'good'
    
    def _calculate_budget_health(self, utilization_rate, variance_percentage, category_analysis):
        """Calculate an overall budget health score (0-100)."""
        # Base score starts at 100
        score = 100
        
        # Penalize for over-utilization
        if utilization_rate > 100:
            score -= (utilization_rate - 100) * 0.5
        
        # Penalize for high variance
        if variance_percentage > 0:
            score -= min(variance_percentage * 0.5, 20)
        
        # Penalize for exceeded categories
        exceeded_categories = sum(
            1 for analysis in category_analysis.values()
            if analysis['status'] == 'exceeded'
        )
        score -= exceeded_categories * 5
        
        # Penalize for warning categories
        warning_categories = sum(
            1 for analysis in category_analysis.values()
            if analysis['status'] == 'warning'
        )
        score -= warning_categories * 2
        
        # Ensure score stays within 0-100
        return max(0, min(100, score))

class FinancialReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def income_statement(self, request):
        """Generate income statement for a given period"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Start date and end date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transactions for the period
        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        )
        
        # Calculate income and expenses
        income = transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        expenses = transactions.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        net_income = income - expenses
        
        return Response({
            'period': {'start': start_date, 'end': end_date},
            'income': income,
            'expenses': expenses,
            'net_income': net_income,
            'categories': {
                'income': self._get_category_breakdown(transactions.filter(type='income')),
                'expenses': self._get_category_breakdown(transactions.filter(type='expense'))
            }
        })
    
    @action(detail=False, methods=['get'])
    def balance_sheet(self, request):
        """Generate balance sheet"""
        # Get all accounts
        accounts = Account.objects.filter(user=request.user)
        
        # Calculate totals
        total_assets = accounts.filter(type__in=['checking', 'savings', 'investment']).aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        total_liabilities = accounts.filter(type__in=['credit', 'loan']).aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        net_worth = total_assets - total_liabilities
        
        return Response({
            'assets': {
                'total': total_assets,
                'breakdown': self._get_account_breakdown(accounts.filter(type__in=['checking', 'savings', 'investment']))
            },
            'liabilities': {
                'total': total_liabilities,
                'breakdown': self._get_account_breakdown(accounts.filter(type__in=['credit', 'loan']))
            },
            'net_worth': net_worth
        })
    
    @action(detail=False, methods=['get'])
    def cash_flow(self, request):
        """Generate cash flow statement"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Start date and end date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transactions for the period
        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        )
        
        # Calculate cash flows
        operating_activities = self._calculate_operating_cash_flow(transactions)
        investing_activities = self._calculate_investing_cash_flow(transactions)
        financing_activities = self._calculate_financing_cash_flow(transactions)
        
        net_cash_flow = operating_activities + investing_activities + financing_activities
        
        return Response({
            'period': {'start': start_date, 'end': end_date},
            'operating_activities': operating_activities,
            'investing_activities': investing_activities,
            'financing_activities': financing_activities,
            'net_cash_flow': net_cash_flow
        })
    
    @action(detail=False, methods=['get'])
    def tax_summary(self, request):
        """Generate tax summary for a given year"""
        year = request.query_params.get('year')
        
        if not year:
            return Response(
                {'error': 'Year is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transactions for the year
        transactions = Transaction.objects.filter(
            user=request.user,
            date__year=year
        )
        
        # Calculate tax-related amounts
        income = transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        deductions = transactions.filter(category__is_tax_deductible=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        taxable_income = income - deductions
        
        return Response({
            'year': year,
            'total_income': income,
            'deductions': deductions,
            'taxable_income': taxable_income,
            'categories': {
                'income': self._get_category_breakdown(transactions.filter(type='income')),
                'deductions': self._get_category_breakdown(
                    transactions.filter(category__is_tax_deductible=True)
                )
            }
        })
    
    @action(detail=False, methods=['get'])
    def investment_performance(self, request):
        """Generate investment performance report"""
        # Get investment accounts
        accounts = Account.objects.filter(
            user=request.user,
            type='investment'
        )
        
        performance_data = []
        for account in accounts:
            # Get historical balances
            balances = account.balance_history.all().order_by('date')
            
            if not balances:
                continue
            
            # Calculate performance metrics
            initial_balance = balances.first().balance
            final_balance = balances.last().balance
            total_return = final_balance - initial_balance
            return_percentage = (total_return / initial_balance * 100) if initial_balance > 0 else 0
            
            performance_data.append({
                'account': account.name,
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_return': total_return,
                'return_percentage': return_percentage,
                'history': [
                    {'date': b.date, 'balance': b.balance}
                    for b in balances
                ]
            })
        
        return Response(performance_data)
    
    @action(detail=False, methods=['get'])
    def debt_analysis(self, request):
        """Generate debt analysis report"""
        # Get debt accounts
        accounts = Account.objects.filter(
            user=request.user,
            type__in=['credit', 'loan']
        )
        
        total_debt = accounts.aggregate(total=Sum('balance'))['total'] or 0
        
        # Calculate debt metrics
        debt_breakdown = []
        for account in accounts:
            # Get payment history
            payments = Transaction.objects.filter(
                account=account,
                type='expense'
            ).order_by('date')
            
            if not payments:
                continue
            
            # Calculate metrics
            total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
            remaining_balance = account.balance
            payment_history = [
                {'date': p.date, 'amount': p.amount}
                for p in payments
            ]
            
            debt_breakdown.append({
                'account': account.name,
                'type': account.type,
                'total_paid': total_paid,
                'remaining_balance': remaining_balance,
                'payment_history': payment_history
            })
        
        return Response({
            'total_debt': total_debt,
            'debt_breakdown': debt_breakdown
        })
    
    def _get_category_breakdown(self, transactions):
        """Helper method to get category breakdown of transactions"""
        return transactions.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
    
    def _get_account_breakdown(self, accounts):
        """Helper method to get account breakdown"""
        return [
            {
                'name': account.name,
                'type': account.type,
                'balance': account.balance
            }
            for account in accounts
        ]
    
    def _calculate_operating_cash_flow(self, transactions):
        """Calculate operating cash flow"""
        income = transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        expenses = transactions.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        return income - expenses
    
    def _calculate_investing_cash_flow(self, transactions):
        """Calculate investing cash flow"""
        return transactions.filter(
            category__type='investment'
        ).aggregate(total=Sum('amount'))['total'] or 0
    
    def _calculate_financing_cash_flow(self, transactions):
        """Calculate financing cash flow"""
        return transactions.filter(
            category__type__in=['loan', 'credit']
        ).aggregate(total=Sum('amount'))['total'] or 0