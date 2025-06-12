from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import DataExport, DataImport, SavedVisualization, DataSync, Backup
import json

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
        self.export = DataExport.objects.create(
            user=self.user,
            export_type='transactions',
            format='csv',
            status='pending'
        )
        
        self.import_job = DataImport.objects.create(
            user=self.user,
            import_type='transactions',
            format='csv',
            status='pending'
        )
        
        self.visualization = SavedVisualization.objects.create(
            user=self.user,
            name='Test Chart',
            chart_type='bar',
            data_source='transactions',
            is_public=False
        )
        
        self.sync = DataSync.objects.create(
            user=self.user,
            sync_type='bank',
            service_name='Test Bank',
            status='pending'
        )
        
        self.backup = Backup.objects.create(
            user=self.user,
            status='pending',
            type='full'
        )

    def test_export_list(self):
        """Test listing exports"""
        url = reverse('export-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_import_list(self):
        """Test listing imports"""
        url = reverse('import-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_visualization_list(self):
        """Test listing visualizations"""
        url = reverse('visualization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_sync_list(self):
        """Test listing sync jobs"""
        url = reverse('sync-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_backup_list(self):
        """Test listing backups"""
        url = reverse('backup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_export(self):
        """Test creating a new export"""
        url = reverse('export-list')
        data = {
            'export_type': 'transactions',
            'format': 'csv',
            'filters': {'start_date': '2024-01-01'}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataExport.objects.count(), 2)

    def test_create_import(self):
        """Test creating a new import"""
        url = reverse('import-list')
        data = {
            'import_type': 'transactions',
            'format': 'csv'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataImport.objects.count(), 2)

    def test_create_visualization(self):
        """Test creating a new visualization"""
        url = reverse('visualization-list')
        data = {
            'name': 'New Chart',
            'chart_type': 'line',
            'data_source': 'transactions',
            'filters': {'start_date': '2024-01-01'},
            'configuration': {'title': 'Test Chart'}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedVisualization.objects.count(), 2)

    def test_create_sync(self):
        """Test creating a new sync job"""
        url = reverse('sync-list')
        data = {
            'sync_type': 'bank',
            'service_name': 'New Bank',
            'configuration': {
                'credentials': {'api_key': 'test_key'},
                'account_number': '123456'
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataSync.objects.count(), 2)

    def test_create_backup(self):
        """Test creating a new backup"""
        url = reverse('backup-list')
        data = {
            'type': 'full',
            'description': 'Test backup'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Backup.objects.count(), 2)

    def test_export_download(self):
        """Test downloading an export"""
        self.export.status = 'completed'
        self.export.save()
        url = reverse('export-download', args=[self.export.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sync_now(self):
        """Test triggering a sync"""
        url = reverse('sync-sync-now', args=[self.sync.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_backup_restore(self):
        """Test restoring a backup"""
        self.backup.status = 'completed'
        self.backup.save()
        url = reverse('backup-restore', args=[self.backup.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) 