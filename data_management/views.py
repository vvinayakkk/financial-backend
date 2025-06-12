from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
import pandas as pd
import json
import csv
import xlsxwriter
from io import BytesIO
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import (
    DataExport, DataImport, SavedVisualization,
    DataSync, Backup
)
from .serializers import (
    DataExportSerializer, DataImportSerializer,
    SavedVisualizationSerializer, DataSyncSerializer,
    BackupSerializer
)
from finances.models import Transaction, Account, Category, Budget
import yfinance as yf
import matplotlib.pyplot as plt
import os
from django.conf import settings
from django.db import models

class DataExportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data exports.
    
    Supports exporting financial data in various formats (CSV, Excel, JSON).
    Export types include transactions, accounts, categories, budgets, and all data.
    """
    serializer_class = DataExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all exports for the authenticated user",
        responses={
            200: DataExportSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new export job",
        request_body=DataExportSerializer,
        responses={
            201: DataExportSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Download the exported file",
        responses={
            200: "File download",
            400: "Export not ready",
            401: "Unauthorized",
            404: "Export not found"
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        export = self.get_object()
        if export.status != 'completed':
            return Response(
                {'error': 'Export is not ready for download.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = HttpResponse(export.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{export.file.name}"'
        return response
    
    def _process_export(self, export):
        """Process the export request"""
        try:
            # Get data based on export type
            data = self._get_export_data(export)
            
            # Generate file based on format
            file_data = self._generate_export_file(data, export.format)
            
            # Save file
            export.file.save(
                f"{export.export_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export.format}",
                file_data
            )
            export.status = 'completed'
            export.save()
        except Exception as e:
            export.status = 'failed'
            export.save()
            raise e
    
    def _get_export_data(self, export):
        """Get data for export based on type"""
        if export.export_type == 'transactions':
            return self._get_transaction_data(export.filters)
        elif export.export_type == 'accounts':
            return self._get_account_data(export.filters)
        elif export.export_type == 'categories':
            return self._get_category_data(export.filters)
        elif export.export_type == 'budgets':
            return self._get_budget_data(export.filters)
        elif export.export_type == 'all':
            return self._get_all_data(export.filters)
        else:
            raise ValueError(f"Unsupported export type: {export.export_type}")
    
    def _generate_export_file(self, data, format):
        """Generate export file in specified format"""
        if format == 'csv':
            return self._generate_csv(data)
        elif format == 'excel':
            return self._generate_excel(data)
        elif format == 'json':
            return self._generate_json(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _get_transaction_data(self, filters):
        """Get transaction data with filters"""
        queryset = Transaction.objects.filter(user=self.request.user)
        # Apply filters
        if 'start_date' in filters:
            queryset = queryset.filter(date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(date__lte=filters['end_date'])
        if 'category' in filters:
            queryset = queryset.filter(category_id=filters['category'])
        if 'account' in filters:
            queryset = queryset.filter(account_id=filters['account'])
        
        return queryset.values()
    
    def _get_account_data(self, filters):
        """Get account data with filters"""
        queryset = Account.objects.filter(user=self.request.user)
        # Apply filters
        if 'type' in filters:
            queryset = queryset.filter(type=filters['type'])
        
        return queryset.values()
    
    def _get_category_data(self, filters):
        """Get category data with filters"""
        queryset = Category.objects.filter(user=self.request.user)
        # Apply filters
        if 'type' in filters:
            queryset = queryset.filter(type=filters['type'])
        
        return queryset.values()
    
    def _get_budget_data(self, filters):
        """Get budget data with filters"""
        queryset = Budget.objects.filter(user=self.request.user)
        # Apply filters
        if 'start_date' in filters:
            queryset = queryset.filter(start_date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(end_date__lte=filters['end_date'])
        
        return queryset.values()
    
    def _get_all_data(self, filters):
        """Get all data with filters"""
        return {
            'transactions': self._get_transaction_data(filters),
            'accounts': self._get_account_data(filters),
            'categories': self._get_category_data(filters),
            'budgets': self._get_budget_data(filters)
        }
    
    def _generate_csv(self, data):
        """Generate CSV file"""
        output = BytesIO()
        if isinstance(data, dict):
            # Multiple sheets
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            for sheet_name, sheet_data in data.items():
                df = pd.DataFrame(sheet_data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            writer.save()
        else:
            # Single sheet
            df = pd.DataFrame(data)
            df.to_csv(output, index=False)
        output.seek(0)
        return output
    
    def _generate_excel(self, data):
        """Generate Excel file"""
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        if isinstance(data, dict):
            # Multiple sheets
            for sheet_name, sheet_data in data.items():
                df = pd.DataFrame(sheet_data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Single sheet
            df = pd.DataFrame(data)
            df.to_excel(writer, index=False)
        
        writer.save()
        output.seek(0)
        return output
    
    def _generate_json(self, data):
        """Generate JSON file"""
        output = BytesIO()
        if isinstance(data, dict):
            json_data = {
                key: list(value) for key, value in data.items()
            }
        else:
            json_data = list(data)
        
        output.write(json.dumps(json_data, default=str).encode())
        output.seek(0)
        return output

class DataImportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data imports.
    
    Supports importing financial data from various formats (CSV, Excel, JSON).
    Import types include transactions, accounts, categories, and budgets.
    """
    serializer_class = DataImportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all imports for the authenticated user",
        responses={
            200: DataImportSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new import job",
        request_body=DataImportSerializer,
        responses={
            201: DataImportSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def get_queryset(self):
        return DataImport.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        import_job = serializer.save(user=self.request.user)
        # Process import asynchronously
        self._process_import(import_job)
    
    def _process_import(self, import_job):
        """Process the import request"""
        try:
            # Read file based on format
            data = self._read_import_file(import_job)
            
            # Process data based on type
            self._process_import_data(import_job, data)
            
            import_job.status = 'completed'
            import_job.save()
        except Exception as e:
            import_job.status = 'failed'
            import_job.error_log = str(e)
            import_job.save()
            raise e
    
    def _read_import_file(self, import_job):
        """Read import file based on format"""
        if import_job.format == 'csv':
            return pd.read_csv(import_job.file)
        elif import_job.format == 'excel':
            return pd.read_excel(import_job.file)
        elif import_job.format == 'json':
            return pd.read_json(import_job.file)
        else:
            raise ValueError(f"Unsupported format: {import_job.format}")
    
    def _process_import_data(self, import_job, data):
        """Process imported data based on type"""
        if import_job.import_type == 'transactions':
            self._import_transactions(import_job, data)
        elif import_job.import_type == 'accounts':
            self._import_accounts(import_job, data)
        elif import_job.import_type == 'categories':
            self._import_categories(import_job, data)
        elif import_job.import_type == 'budgets':
            self._import_budgets(import_job, data)
        else:
            raise ValueError(f"Unsupported import type: {import_job.import_type}")
    
    @transaction.atomic
    def _import_transactions(self, import_job, data):
        """Import transactions"""
        for _, row in data.iterrows():
            try:
                Transaction.objects.create(
                    user=import_job.user,
                    account_id=row['account_id'],
                    category_id=row['category_id'],
                    amount=row['amount'],
                    date=row['date'],
                    description=row['description'],
                    type=row['type']
                )
                import_job.processed_records += 1
            except Exception as e:
                import_job.failed_records += 1
                import_job.error_log += f"\nError processing row {_}: {str(e)}"
    
    @transaction.atomic
    def _import_accounts(self, import_job, data):
        """Import accounts"""
        for _, row in data.iterrows():
            try:
                Account.objects.create(
                    user=import_job.user,
                    name=row['name'],
                    type=row['type'],
                    balance=row['balance'],
                    currency=row['currency']
                )
                import_job.processed_records += 1
            except Exception as e:
                import_job.failed_records += 1
                import_job.error_log += f"\nError processing row {_}: {str(e)}"
    
    @transaction.atomic
    def _import_categories(self, import_job, data):
        """Import categories"""
        for _, row in data.iterrows():
            try:
                Category.objects.create(
                    user=import_job.user,
                    name=row['name'],
                    type=row['type'],
                    parent_id=row.get('parent_id')
                )
                import_job.processed_records += 1
            except Exception as e:
                import_job.failed_records += 1
                import_job.error_log += f"\nError processing row {_}: {str(e)}"
    
    @transaction.atomic
    def _import_budgets(self, import_job, data):
        """Import budgets"""
        for _, row in data.iterrows():
            try:
                Budget.objects.create(
                    user=import_job.user,
                    category_id=row['category_id'],
                    amount=row['amount'],
                    start_date=row['start_date'],
                    end_date=row['end_date']
                )
                import_job.processed_records += 1
            except Exception as e:
                import_job.failed_records += 1
                import_job.error_log += f"\nError processing row {_}: {str(e)}"

class SavedVisualizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing saved visualizations.
    
    Supports creating and managing various chart types (line, bar, pie, scatter, area, radar).
    Data sources include transactions, budgets, and accounts.
    """
    serializer_class = SavedVisualizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all visualizations for the authenticated user",
        responses={
            200: SavedVisualizationSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new visualization",
        request_body=SavedVisualizationSerializer,
        responses={
            201: SavedVisualizationSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get visualization data",
        responses={
            200: "Visualization data",
            401: "Unauthorized",
            404: "Visualization not found"
        }
    )
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        visualization = self.get_object()
        data = self._get_visualization_data(visualization)
        return Response(data)
    
    def get_queryset(self):
        return SavedVisualization.objects.filter(
            user=self.request.user
        ) | SavedVisualization.objects.filter(is_public=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def _get_visualization_data(self, visualization):
        """Get data for visualization"""
        if visualization.data_source == 'transactions':
            return self._get_transaction_data(visualization.filters)
        elif visualization.data_source == 'budgets':
            return self._get_budget_data(visualization.filters)
        elif visualization.data_source == 'accounts':
            return self._get_account_data(visualization.filters)
        else:
            raise ValueError(f"Unsupported data source: {visualization.data_source}")
    
    def _get_transaction_data(self, filters):
        """Get transaction data for visualization"""
        queryset = Transaction.objects.filter(user=self.request.user)
        # Apply filters
        if 'start_date' in filters:
            queryset = queryset.filter(date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(date__lte=filters['end_date'])
        if 'category' in filters:
            queryset = queryset.filter(category_id=filters['category'])
        if 'type' in filters:
            queryset = queryset.filter(type=filters['type'])
        
        # Group and aggregate data
        if filters.get('group_by') == 'category':
            return queryset.values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')
        elif filters.get('group_by') == 'date':
            return queryset.values('date').annotate(
                total=Sum('amount')
            ).order_by('date')
        else:
            return queryset.values('date', 'amount', 'category__name', 'type')
    
    def _get_budget_data(self, filters):
        """Get budget data for visualization"""
        queryset = Budget.objects.filter(user=self.request.user)
        # Apply filters
        if 'start_date' in filters:
            queryset = queryset.filter(start_date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(end_date__lte=filters['end_date'])
        
        # Get actual spending
        transactions = Transaction.objects.filter(
            user=self.request.user,
            date__range=[filters.get('start_date'), filters.get('end_date')]
        )
        
        budget_data = []
        for budget in queryset:
            spent = transactions.filter(
                category=budget.category
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            budget_data.append({
                'category': budget.category.name,
                'budgeted': budget.amount,
                'spent': spent,
                'remaining': budget.amount - spent
            })
        
        return budget_data
    
    def _get_account_data(self, filters):
        """Get account data for visualization"""
        queryset = Account.objects.filter(user=self.request.user)
        # Apply filters
        if 'type' in filters:
            queryset = queryset.filter(type=filters['type'])
        
        return queryset.values('name', 'type', 'balance', 'currency')

class DataSyncViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data synchronization with external services.
    
    Supports syncing with:
    - Bank accounts
    - Investment accounts
    - Tax software
    - Accounting software
    """
    serializer_class = DataSyncSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all sync jobs for the authenticated user",
        responses={
            200: DataSyncSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new sync job",
        request_body=DataSyncSerializer,
        responses={
            201: DataSyncSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def get_queryset(self):
        return DataSync.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        sync = serializer.save(user=self.request.user)
        # Start sync process asynchronously
        self._start_sync(sync)
    
    @swagger_auto_schema(
        operation_description="Trigger a sync job immediately",
        responses={
            200: "Sync started",
            401: "Unauthorized",
            404: "Sync job not found"
        }
    )
    @action(detail=True, methods=['post'])
    def sync_now(self, request, pk=None):
        sync = self.get_object()
        self._start_sync(sync)
        return Response({'status': 'Sync started'})
    
    def _start_sync(self, sync):
        """Start synchronization process"""
        try:
            if sync.sync_type == 'bank':
                self._sync_bank_account(sync)
            elif sync.sync_type == 'investment':
                self._sync_investment_account(sync)
            elif sync.sync_type == 'tax':
                self._sync_tax_software(sync)
            elif sync.sync_type == 'accounting':
                self._sync_accounting_software(sync)
            else:
                raise ValueError(f"Unsupported sync type: {sync.sync_type}")
            
            sync.status = 'completed'
            sync.last_sync = timezone.now()
            sync.save()
        except Exception as e:
            sync.status = 'failed'
            sync.error_log = str(e)
            sync.save()
            raise e
    
    def _sync_bank_account(self, sync):
        """Sync bank account data (simulate fetch from bank API)"""
        # Example: Use sync.configuration for credentials/API keys
        credentials = sync.configuration.get('credentials', {})
        account_number = sync.configuration.get('account_number')
        # Simulate fetching transactions and balances
        # In production, replace this with a real bank API client (e.g., Plaid, Yodlee)
        fetched_transactions = [
            {
                'date': timezone.now().date(),
                'amount': 1000.0,
                'description': 'Salary',
                'type': 'income',
                'category': 'Salary',
            },
            {
                'date': timezone.now().date(),
                'amount': -50.0,
                'description': 'Groceries',
                'type': 'expense',
                'category': 'Groceries',
            },
        ]
        # Create or update account
        account, _ = Account.objects.get_or_create(
            user=sync.user,
            name=sync.service_name,
            defaults={'type': 'bank', 'balance': 0, 'currency': 'USD'}
        )
        # Add transactions
        for tx in fetched_transactions:
            Transaction.objects.create(
                user=sync.user,
                account=account,
                amount=abs(tx['amount']),
                type=tx['type'],
                date=tx['date'],
                description=tx['description'],
                category=Category.objects.filter(user=sync.user, name=tx['category']).first()
            )
        # Update account balance
        account.balance = sum(tx['amount'] for tx in fetched_transactions)
        account.save()

    def _sync_investment_account(self, sync):
        """Sync investment account data (simulate fetch using yfinance)"""
        symbols = sync.configuration.get('symbols', ['AAPL', 'GOOGL'])
        account, _ = Account.objects.get_or_create(
            user=sync.user,
            name=sync.service_name,
            defaults={'type': 'investment', 'balance': 0, 'currency': 'USD'}
        )
        total_value = 0
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1mo')
            latest = hist.tail(1)
            if not latest.empty:
                price = float(latest['Close'].iloc[0])
                shares = sync.configuration.get('holdings', {}).get(symbol, 10)
                value = price * shares
                total_value += value
                # Log as a transaction (for demonstration)
                Transaction.objects.create(
                    user=sync.user,
                    account=account,
                    amount=value,
                    type='income',
                    date=timezone.now().date(),
                    description=f'Investment value for {symbol}',
                    category=None
                )
        account.balance = total_value
        account.save()

    def _sync_tax_software(self, sync):
        """Sync tax software data (simulate export of transactions)"""
        # Simulate exporting all transactions for the user in the last year
        start_date = timezone.now().date().replace(month=1, day=1)
        transactions = Transaction.objects.filter(user=sync.user, date__gte=start_date)
        export_data = list(transactions.values('date', 'amount', 'type', 'description'))
        # In production, upload this data to the tax software API or generate a file
        sync.error_log = json.dumps(export_data, default=str)[:1000]  # Store a preview in error_log

    def _sync_accounting_software(self, sync):
        """Sync accounting software data (simulate export of accounts and transactions)"""
        accounts = Account.objects.filter(user=sync.user)
        transactions = Transaction.objects.filter(user=sync.user)
        export_data = {
            'accounts': list(accounts.values('name', 'type', 'balance', 'currency')),
            'transactions': list(transactions.values('date', 'amount', 'type', 'description')),
        }
        # In production, upload this data to the accounting software API or generate a file
        sync.error_log = json.dumps(export_data, default=str)[:1000]  # Store a preview in error_log

class BackupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data backups.
    
    Supports creating full and incremental backups of user data.
    Includes restore functionality for data recovery.
    """
    serializer_class = BackupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all backups for the authenticated user",
        responses={
            200: BackupSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new backup",
        request_body=BackupSerializer,
        responses={
            201: BackupSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Restore data from a backup",
        responses={
            200: "Restore completed",
            400: "Backup not ready",
            401: "Unauthorized",
            404: "Backup not found",
            500: "Restore failed"
        }
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        backup = self.get_object()
        if backup.status != 'completed':
            return Response(
                {'error': 'Backup is not ready for restoration.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            self._restore_backup(backup)
            return Response({'status': 'Restore completed'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_backup(self, backup):
        """Create backup of user data"""
        try:
            # Get all user data
            data = {
                'transactions': list(Transaction.objects.filter(user=backup.user).values()),
                'accounts': list(Account.objects.filter(user=backup.user).values()),
                'categories': list(Category.objects.filter(user=backup.user).values()),
                'budgets': list(Budget.objects.filter(user=backup.user).values())
            }
            
            # Create backup file
            output = BytesIO()
            json.dump(data, output, default=str)
            output.seek(0)
            
            # Save backup file
            backup.file.save(
                f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json",
                output
            )
            backup.size = output.tell()
            backup.status = 'completed'
            backup.save()
        except Exception as e:
            backup.status = 'failed'
            backup.save()
            raise e
    
    def _restore_backup(self, backup):
        """Restore data from backup"""
        try:
            # Read backup file
            data = json.load(backup.file)
            
            # Restore data
            with transaction.atomic():
                # Clear existing data
                Transaction.objects.filter(user=backup.user).delete()
                Account.objects.filter(user=backup.user).delete()
                Category.objects.filter(user=backup.user).delete()
                Budget.objects.filter(user=backup.user).delete()
                
                # Restore categories
                for category in data['categories']:
                    Category.objects.create(user=backup.user, **category)
                
                # Restore accounts
                for account in data['accounts']:
                    Account.objects.create(user=backup.user, **account)
                
                # Restore budgets
                for budget in data['budgets']:
                    Budget.objects.create(user=backup.user, **budget)
                
                # Restore transactions
                for transaction in data['transactions']:
                    Transaction.objects.create(user=backup.user, **transaction)
        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")

def generate_visualizations(transactions):
    """Generate various visualizations for transactions"""
    # Weekly transactions pie chart
    weekly_transactions = transactions.filter(term='weekly')
    weekly_categories = weekly_transactions.values('category').annotate(total=models.Count('category'))
    weekly_labels = [item['category'] for item in weekly_categories]
    weekly_totals = [item['total'] for item in weekly_categories]

    plt.figure(figsize=(8, 6))
    plt.pie(weekly_totals, labels=weekly_labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.tab20.colors)
    plt.title('Weekly Transaction Categories', fontsize=16)
    plt.axis('equal')
    weekly_pie_chart_path = os.path.join(settings.MEDIA_ROOT, 'visualizations', 'weekly_pie_chart.png')
    os.makedirs(os.path.dirname(weekly_pie_chart_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(weekly_pie_chart_path)
    plt.close()

    # Weekly transactions bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(weekly_labels, weekly_totals, color=plt.cm.tab20.colors)
    plt.xlabel('Weekly Transaction Categories', fontsize=14)
    plt.ylabel('Total Amount', fontsize=14)
    plt.title('Weekly Transaction Amounts', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()
    weekly_bar_chart_path = os.path.join(settings.MEDIA_ROOT, 'visualizations', 'weekly_bar_chart.png')
    plt.savefig(weekly_bar_chart_path)
    plt.close()

    # Monthly transactions bar chart
    monthly_transactions = transactions.filter(term='monthly')
    monthly_categories = monthly_transactions.values('category').annotate(total_amount=models.Sum('amount'))
    monthly_labels = [item['category'] for item in monthly_categories]
    monthly_totals = [item['total_amount'] for item in monthly_categories]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(monthly_labels, monthly_totals, color=plt.cm.tab20.colors)
    plt.xlabel('Monthly Transaction Categories', fontsize=14)
    plt.ylabel('Total Amount', fontsize=14)
    plt.title('Monthly Transaction Amounts', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()

    # Add total amounts as labels on top of each bar
    for bar, total in zip(bars, monthly_totals):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100, f'{total}', ha='center', va='bottom')

    monthly_bar_chart_path = os.path.join(settings.MEDIA_ROOT, 'visualizations', 'monthly_bar_chart.png')
    plt.savefig(monthly_bar_chart_path)
    plt.close()

    # Yearly transactions bar chart
    yearly_transactions = transactions.filter(term='yearly')
    yearly_categories = yearly_transactions.values('category').annotate(total_amount=models.Sum('amount'))
    yearly_labels = [item['category'] for item in yearly_categories]
    yearly_totals = [item['total_amount'] for item in yearly_categories]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(yearly_labels, yearly_totals, color=plt.cm.tab20.colors)
    plt.xlabel('Yearly Transaction Categories', fontsize=14)
    plt.ylabel('Total Amount', fontsize=14)
    plt.title('Yearly Transaction Amounts', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()

    # Add total amounts as labels on top of each bar
    for bar, total in zip(bars, yearly_totals):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100, f'{total}', ha='center', va='bottom')

    yearly_bar_chart_path = os.path.join(settings.MEDIA_ROOT, 'visualizations', 'yearly_bar_chart.png')
    plt.savefig(yearly_bar_chart_path)
    plt.close()

    return {
        'weekly_pie_chart': weekly_pie_chart_path,
        'weekly_bar_chart': weekly_bar_chart_path,
        'monthly_bar_chart': monthly_bar_chart_path,
        'yearly_bar_chart': yearly_bar_chart_path
    }
