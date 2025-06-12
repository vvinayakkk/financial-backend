from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import (
    BillUpload, StockNews, AIRecommendation,
    FinancialInsight, StockPortfolio, MarketAnalysis
)
from finances.models import Transaction, Category, Account
from decimal import Decimal
import json
from unittest.mock import patch, MagicMock

User = get_user_model()

class AIFeaturesTests(TestCase):
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

    @patch('ai_features.services.AIService.generate_financial_recommendations')
    def test_get_recommendations(self, mock_generate):
        """Test getting AI recommendations"""
        # Mock the AI service response
        mock_recommendations = [
            {
                'type': 'savings',
                'title': 'Test Recommendation',
                'description': 'Test description',
                'confidence_score': 0.8,
                'priority': 'high'
            }
        ]
        mock_generate.return_value = mock_recommendations
        
        url = reverse('ai-recommendations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('ai_features.services.AIService.analyze_stock_news')
    def test_stock_news_analysis(self, mock_analyze):
        """Test stock news analysis"""
        # Mock the AI service response
        mock_news = [
            {
                'symbol': 'AAPL',
                'title': 'Test News',
                'content': 'Test content',
                'sentiment_score': 0.8,
                'impact_score': 0.7
            }
        ]
        mock_analyze.return_value = mock_news
        
        url = reverse('stock-news-analyze')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('ai_features.services.AIService.generate_market_analysis')
    def test_market_analysis(self, mock_analyze):
        """Test market analysis generation"""
        # Mock the AI service response
        mock_analysis = {
            'symbol': 'AAPL',
            'technical_indicators': {
                'sma_20': 150.0,
                'rsi': 65.0
            },
            'fundamental_metrics': {
                'pe_ratio': 25.0,
                'market_cap': 2000000000000
            },
            'ai_prediction': {
                'short_term': 160.0,
                'medium_term': 170.0,
                'long_term': 180.0
            }
        }
        mock_analyze.return_value = mock_analysis
        
        url = reverse('market-analysis-analyze')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['symbol'], 'AAPL')

    def test_bill_upload(self):
        """Test bill upload and processing"""
        url = reverse('bill-upload-list')
        data = {
            'file': 'test_bill.pdf',
            'category': self.category.id
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BillUpload.objects.count(), 1)

    def test_financial_insights(self):
        """Test financial insights generation"""
        url = reverse('financial-insights-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stock_portfolio(self):
        """Test stock portfolio management"""
        # Create a test portfolio
        portfolio = StockPortfolio.objects.create(
            user=self.user,
            symbol='AAPL',
            shares=10,
            average_price=Decimal('150.00')
        )
        
        url = reverse('stock-portfolio-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_portfolio_summary(self):
        """Test portfolio summary generation"""
        # Create test portfolio items
        StockPortfolio.objects.create(
            user=self.user,
            symbol='AAPL',
            shares=10,
            average_price=Decimal('150.00')
        )
        StockPortfolio.objects.create(
            user=self.user,
            symbol='GOOGL',
            shares=5,
            average_price=Decimal('2000.00')
        )
        
        url = reverse('stock-portfolio-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_value', response.data)
        self.assertIn('total_cost', response.data)

    def test_market_trends(self):
        """Test market trends analysis"""
        url = reverse('market-analysis-trends')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_technical_indicators(self):
        """Test technical indicators calculation"""
        url = reverse('market-analysis-technical-indicators')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        # Create test news items
        StockNews.objects.create(
            symbol='AAPL',
            title='Test News 1',
            content='Positive news content',
            sentiment_score=0.8,
            impact_score=0.7
        )
        StockNews.objects.create(
            symbol='AAPL',
            title='Test News 2',
            content='Negative news content',
            sentiment_score=-0.5,
            impact_score=0.6
        )
        
        url = reverse('market-analysis-sentiment')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('average_sentiment', response.data)
        self.assertIn('recent_news', response.data)

    def test_risk_metrics(self):
        """Test risk metrics calculation"""
        url = reverse('market-analysis-risk-metrics')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('volatility', response.data)
        self.assertIn('beta', response.data)

    def test_correlation_analysis(self):
        """Test correlation analysis"""
        url = reverse('market-analysis-correlation')
        response = self.client.get(url, {'symbol': 'AAPL'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('correlations', response.data) 