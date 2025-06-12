from rest_framework import serializers
from .models import (
    BillUpload, StockNews, AIRecommendation,
    FinancialInsight, StockPortfolio, MarketAnalysis
)

class BillUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillUpload
        fields = ['id', 'file', 'uploaded_at', 'processed', 'extracted_data', 'transaction']
        read_only_fields = ['uploaded_at', 'processed', 'extracted_data', 'transaction']

class StockNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockNews
        fields = ['id', 'symbol', 'title', 'content', 'source', 'published_at',
                 'sentiment_score', 'impact_score', 'created_at']
        read_only_fields = ['created_at']

class AIRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendation
        fields = ['id', 'type', 'title', 'description', 'confidence_score',
                 'context_data', 'created_at', 'is_read', 'action_taken']
        read_only_fields = ['created_at']

class FinancialInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialInsight
        fields = ['id', 'type', 'title', 'description', 'data_points',
                 'created_at', 'is_read']
        read_only_fields = ['created_at']

class StockPortfolioSerializer(serializers.ModelSerializer):
    current_value = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()

    class Meta:
        model = StockPortfolio
        fields = ['id', 'symbol', 'shares', 'average_price', 'current_price',
                 'current_value', 'profit_loss', 'profit_loss_percentage',
                 'last_updated']
        read_only_fields = ['current_price', 'last_updated']

    def get_current_value(self, obj):
        if obj.current_price:
            return float(obj.shares * obj.current_price)
        return None

    def get_profit_loss(self, obj):
        if obj.current_price:
            return float((obj.current_price - obj.average_price) * obj.shares)
        return None

    def get_profit_loss_percentage(self, obj):
        if obj.current_price and obj.average_price:
            return float((obj.current_price - obj.average_price) / obj.average_price * 100)
        return None

class MarketAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketAnalysis
        fields = ['id', 'symbol', 'analysis_date', 'technical_indicators',
                 'fundamental_metrics', 'ai_prediction', 'confidence_score',
                 'created_at']
        read_only_fields = ['created_at'] 