from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from health_check.views import MainView
from health_check.db.views import DatabaseView
from health_check.cache.views import CacheView
from health_check.storage.views import StorageView
from health_check.contrib.redis.views import RedisView
from health_check.contrib.celery.views import CeleryView

schema_view = get_schema_view(
    openapi.Info(
        title="Financial Tracker API",
        default_version='v1',
        description="API documentation for the Financial Tracker system",
        terms_of_service="https://www.financial-tracker.com/terms/",
        contact=openapi.Contact(email="contact@financial-tracker.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication and User Management
    path('api/users/', include('users.urls')),
    
    # Financial Management
    path('api/finances/', include('finances.urls')),
    
    # Data Management
    path('api/data/', include('data_management.urls')),
    
    # Health Check
    path('health/', MainView.as_view(), name='health_check'),
    path('health/db/', DatabaseView.as_view(), name='health_check_db'),
    path('health/cache/', CacheView.as_view(), name='health_check_cache'),
    path('health/storage/', StorageView.as_view(), name='health_check_storage'),
    path('health/redis/', RedisView.as_view(), name='health_check_redis'),
    path('health/celery/', CeleryView.as_view(), name='health_check_celery'),
    
    # AI Features
    path('api/ai/', include('ai_features.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 