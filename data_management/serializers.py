from rest_framework import serializers
from .models import (
    DataExport, DataImport, SavedVisualization,
    DataSync, Backup
)

class DataExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataExport
        fields = [
            'id', 'export_type', 'format', 'file',
            'created_at', 'status', 'filters'
        ]
        read_only_fields = ['file', 'created_at', 'status']

class DataImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataImport
        fields = [
            'id', 'import_type', 'format', 'file',
            'created_at', 'status', 'processed_records',
            'failed_records', 'error_log'
        ]
        read_only_fields = [
            'created_at', 'status', 'processed_records',
            'failed_records', 'error_log'
        ]

class SavedVisualizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedVisualization
        fields = [
            'id', 'name', 'chart_type', 'data_source',
            'filters', 'configuration', 'created_at',
            'updated_at', 'is_public'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DataSyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSync
        fields = [
            'id', 'sync_type', 'service_name', 'last_sync',
            'status', 'configuration', 'error_log'
        ]
        read_only_fields = ['last_sync', 'status', 'error_log']

class BackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backup
        fields = [
            'id', 'file', 'created_at', 'size',
            'status', 'type', 'description'
        ]
        read_only_fields = ['file', 'created_at', 'size', 'status'] 