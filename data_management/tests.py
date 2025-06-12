from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import (
    DataExport, DataImport, SavedVisualization,
    DataSync, Backup
)
from finances.models import Transaction, Category, Account
from decimal import Decimal
import json
from unittest.mock import patch, MagicMock
import os
from django.conf import settings

User = get_user_model()

class DataManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.category = Category.objects.create(
            user=self.user,
            name='Test Category',
            type='expense'
        )
        
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            type='checking',
            balance=Decimal('1000.00')
        )
        
        # Create test transactions
        for _ in range(5):
            Transaction.objects.create(
                user=self.user,
                account=self.account,
                category=self.category,
                amount=Decimal('100.00'),
                type='expense',
                description='Test transaction'
            )

    def test_data_export_creation(self):
        """Test creating a data export"""
        url = reverse('dataexport-list')
        data = {
            'format': 'csv',
            'data_type': 'transactions',
            'date_range': 'last_month'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataExport.objects.count(), 1)

    def test_data_export_download(self):
        """Test downloading a data export"""
        export = DataExport.objects.create(
            user=self.user,
            format='csv',
            data_type='transactions',
            date_range='last_month',
            status='completed',
            file_path='test_export.csv'
        )
        
        url = reverse('dataexport-download', args=[export.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_data_import_creation(self):
        """Test creating a data import"""
        url = reverse('dataimport-list')
        data = {
            'format': 'csv',
            'data_type': 'transactions',
            'file': 'test_import.csv'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataImport.objects.count(), 1)

    def test_data_import_validation(self):
        """Test data import validation"""
        import_job = DataImport.objects.create(
            user=self.user,
            format='csv',
            data_type='transactions',
            status='pending'
        )
        
        url = reverse('dataimport-validate', args=[import_job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('validation_results', response.data)

    def test_saved_visualization_creation(self):
        """Test creating a saved visualization"""
        url = reverse('savedvisualization-list')
        data = {
            'name': 'Test Visualization',
            'type': 'bar_chart',
            'config': json.dumps({
                'data_type': 'transactions',
                'group_by': 'category'
            })
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedVisualization.objects.count(), 1)

    def test_visualization_data(self):
        """Test getting visualization data"""
        visualization = SavedVisualization.objects.create(
            user=self.user,
            name='Test Visualization',
            type='bar_chart',
            config=json.dumps({
                'data_type': 'transactions',
                'group_by': 'category'
            })
        )
        
        url = reverse('savedvisualization-data', args=[visualization.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_data_sync_creation(self):
        """Test creating a data sync job"""
        url = reverse('datasync-list')
        data = {
            'source': 'bank_api',
            'sync_type': 'transactions',
            'frequency': 'daily'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataSync.objects.count(), 1)

    def test_sync_trigger(self):
        """Test triggering a sync job"""
        sync_job = DataSync.objects.create(
            user=self.user,
            source='bank_api',
            sync_type='transactions',
            frequency='daily',
            status='pending'
        )
        
        url = reverse('datasync-trigger', args=[sync_job.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_backup_creation(self):
        """Test creating a backup"""
        url = reverse('backup-list')
        data = {
            'backup_type': 'full',
            'description': 'Test backup'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Backup.objects.count(), 1)

    def test_backup_restore(self):
        """Test restoring a backup"""
        backup = Backup.objects.create(
            user=self.user,
            backup_type='full',
            description='Test backup',
            status='completed',
            file_path='test_backup.zip'
        )
        
        url = reverse('backup-restore', args=[backup.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'restoring')

    def test_export_list(self):
        """Test listing exports"""
        # Create test exports
        for _ in range(3):
            DataExport.objects.create(
                user=self.user,
                format='csv',
                data_type='transactions',
                date_range='last_month',
                status='completed'
            )
        
        url = reverse('dataexport-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_import_list(self):
        """Test listing imports"""
        # Create test imports
        for _ in range(3):
            DataImport.objects.create(
                user=self.user,
                format='csv',
                data_type='transactions',
                status='completed'
            )
        
        url = reverse('dataimport-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_visualization_list(self):
        """Test listing visualizations"""
        # Create test visualizations
        for _ in range(3):
            SavedVisualization.objects.create(
                user=self.user,
                name=f'Test Visualization {_}',
                type='bar_chart',
                config=json.dumps({
                    'data_type': 'transactions',
                    'group_by': 'category'
                })
            )
        
        url = reverse('savedvisualization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_sync_list(self):
        """Test listing sync jobs"""
        # Create test sync jobs
        for _ in range(3):
            DataSync.objects.create(
                user=self.user,
                source='bank_api',
                sync_type='transactions',
                frequency='daily',
                status='completed'
            )
        
        url = reverse('datasync-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_backup_list(self):
        """Test listing backups"""
        # Create test backups
        for _ in range(3):
            Backup.objects.create(
                user=self.user,
                backup_type='full',
                description=f'Test backup {_}',
                status='completed'
            )
        
        url = reverse('backup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_export_delete(self):
        """Test deleting an export"""
        export = DataExport.objects.create(
            user=self.user,
            format='csv',
            data_type='transactions',
            date_range='last_month',
            status='completed'
        )
        
        url = reverse('dataexport-detail', args=[export.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DataExport.objects.count(), 0)

    def test_visualization_delete(self):
        """Test deleting a visualization"""
        visualization = SavedVisualization.objects.create(
            user=self.user,
            name='Test Visualization',
            type='bar_chart',
            config=json.dumps({
                'data_type': 'transactions',
                'group_by': 'category'
            })
        )
        
        url = reverse('savedvisualization-detail', args=[visualization.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SavedVisualization.objects.count(), 0)

    def test_sync_delete(self):
        """Test deleting a sync job"""
        sync_job = DataSync.objects.create(
            user=self.user,
            source='bank_api',
            sync_type='transactions',
            frequency='daily',
            status='completed'
        )
        
        url = reverse('datasync-detail', args=[sync_job.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DataSync.objects.count(), 0)

    def test_backup_delete(self):
        """Test deleting a backup"""
        backup = Backup.objects.create(
            user=self.user,
            backup_type='full',
            description='Test backup',
            status='completed'
        )
        
        url = reverse('backup-detail', args=[backup.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Backup.objects.count(), 0) 