from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BillUploadViewSet, StockNewsViewSet, AIRecommendationViewSet,
    FinancialInsightViewSet, StockPortfolioViewSet, MarketAnalysisViewSet
)

router = DefaultRouter()
router.register(r'bills', BillUploadViewSet, basename='bill')
router.register(r'news', StockNewsViewSet, basename='news')
router.register(r'recommendations', AIRecommendationViewSet, basename='recommendation')
router.register(r'insights', FinancialInsightViewSet, basename='insight')
router.register(r'portfolio', StockPortfolioViewSet, basename='portfolio')
router.register(r'analysis', MarketAnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
] 