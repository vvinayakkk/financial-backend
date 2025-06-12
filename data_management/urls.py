from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DataExportViewSet,
    DataImportViewSet,
    SavedVisualizationViewSet,
    DataSyncViewSet,
    BackupViewSet
)

router = DefaultRouter()
router.register(r'exports', DataExportViewSet, basename='export')
router.register(r'imports', DataImportViewSet, basename='import')
router.register(r'visualizations', SavedVisualizationViewSet, basename='visualization')
router.register(r'sync', DataSyncViewSet, basename='sync')
router.register(r'backups', BackupViewSet, basename='backup')

urlpatterns = [
    path('', include(router.urls)),
] 