from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .models import (
    BillUpload, StockNews, AIRecommendation,
    FinancialInsight, StockPortfolio, MarketAnalysis
)
from .serializers import (
    BillUploadSerializer, StockNewsSerializer, AIRecommendationSerializer,
    FinancialInsightSerializer, StockPortfolioSerializer, MarketAnalysisSerializer
)
from .services import AIService
import yfinance as yf
from django.db import transaction

class BillUploadViewSet(viewsets.ModelViewSet):
    serializer_class = BillUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BillUpload.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        bill_upload = serializer.save(user=self.request.user)
        # Process bill asynchronously
        AIService().process_bill_upload(bill_upload)

class StockNewsViewSet(viewsets.ModelViewSet):
    serializer_class = StockNewsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StockNews.objects.all()
    
    @action(detail=False, methods=['get'])
    def analyze(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        news = AIService().analyze_stock_news(symbol)
        return Response(StockNewsSerializer(news, many=True).data)

class AIRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = AIRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def generate(self, request):
        recommendations = AIService().generate_financial_recommendations(request.user)
        return Response(AIRecommendationSerializer(recommendations, many=True).data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.is_read = True
        recommendation.save()
        return Response(AIRecommendationSerializer(recommendation).data)
    
    @action(detail=True, methods=['post'])
    def mark_action_taken(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.action_taken = True
        recommendation.save()
        return Response(AIRecommendationSerializer(recommendation).data)

class FinancialInsightViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FinancialInsight.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        insight = self.get_object()
        insight.is_read = True
        insight.save()
        return Response(FinancialInsightSerializer(insight).data)

class StockPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = StockPortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StockPortfolio.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        portfolio = self.get_queryset()
        
        # Calculate portfolio metrics
        total_value = sum(item.current_value or 0 for item in portfolio)
        total_cost = sum(item.shares * item.average_price for item in portfolio)
        total_profit_loss = total_value - total_cost
        profit_loss_percentage = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        # Get top performing stocks
        top_performers = sorted(
            portfolio,
            key=lambda x: x.profit_loss_percentage or 0,
            reverse=True
        )[:5]
        
        # Get worst performing stocks
        worst_performers = sorted(
            portfolio,
            key=lambda x: x.profit_loss_percentage or 0
        )[:5]
        
        return Response({
            'total_value': total_value,
            'total_cost': total_cost,
            'total_profit_loss': total_profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'top_performers': StockPortfolioSerializer(top_performers, many=True).data,
            'worst_performers': StockPortfolioSerializer(worst_performers, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def performance_chart(self, request):
        portfolio = self.get_queryset()
        days = int(request.query_params.get('days', 30))
        
        # Get historical data for each stock
        performance_data = {}
        for item in portfolio:
            stock = yf.Ticker(item.symbol)
            hist = stock.history(period=f"{days}d")
            
            # Calculate daily portfolio value
            daily_values = []
            for date, row in hist.iterrows():
                value = item.shares * row['Close']
                daily_values.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
            
            performance_data[item.symbol] = daily_values
        
        return Response(performance_data)
    
    @action(detail=False, methods=['get'])
    def allocation_chart(self, request):
        portfolio = self.get_queryset()
        
        # Calculate allocation percentages
        total_value = sum(item.current_value or 0 for item in portfolio)
        allocation = [
            {
                'symbol': item.symbol,
                'value': item.current_value or 0,
                'percentage': (item.current_value / total_value * 100) if total_value > 0 else 0
            }
            for item in portfolio
        ]
        
        return Response(allocation)

class MarketAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = MarketAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MarketAnalysis.objects.all()
    
    @action(detail=False, methods=['get'])
    def analyze(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analysis = AIService().generate_market_analysis(symbol)
        return Response(MarketAnalysisSerializer(analysis).data)
    
    @action(detail=False, methods=['get'])
    def technical_indicators(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get latest analysis
        analysis = MarketAnalysis.objects.filter(symbol=symbol).order_by('-analysis_date').first()
        if not analysis:
            return Response(
                {'error': 'No analysis found for the symbol.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(analysis.technical_indicators)
    
    @action(detail=False, methods=['get'])
    def price_prediction(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get latest analysis
        analysis = MarketAnalysis.objects.filter(symbol=symbol).order_by('-analysis_date').first()
        if not analysis:
            return Response(
                {'error': 'No analysis found for the symbol.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(analysis.ai_prediction.get('price_prediction', {}))
    
    @action(detail=False, methods=['get'])
    def sentiment_analysis(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get recent news with sentiment scores
        news = StockNews.objects.filter(symbol=symbol).order_by('-published_at')[:10]
        
        # Calculate average sentiment
        avg_sentiment = news.aggregate(avg=Avg('sentiment_score'))['avg'] or 0
        avg_impact = news.aggregate(avg=Avg('impact_score'))['avg'] or 0
        
        return Response({
            'average_sentiment': avg_sentiment,
            'average_impact': avg_impact,
            'recent_news': StockNewsSerializer(news, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def market_trends(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        
        # Calculate trends
        trends = {
            'price_trend': {
                'direction': 'up' if hist['Close'].iloc[-1] > hist['Close'].iloc[0] else 'down',
                'percentage_change': ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)
            },
            'volume_trend': {
                'direction': 'up' if hist['Volume'].iloc[-1] > hist['Volume'].iloc[0] else 'down',
                'percentage_change': ((hist['Volume'].iloc[-1] - hist['Volume'].iloc[0]) / hist['Volume'].iloc[0] * 100)
            },
            'volatility': hist['Close'].pct_change().std() * 100,
            'moving_averages': {
                'sma_20': hist['Close'].rolling(window=20).mean().iloc[-1],
                'sma_50': hist['Close'].rolling(window=50).mean().iloc[-1],
                'sma_200': hist['Close'].rolling(window=200).mean().iloc[-1]
            }
        }
        
        return Response(trends)
    
    @action(detail=False, methods=['get'])
    def correlation_analysis(self, request):
        symbols = request.query_params.get('symbols', '').split(',')
        if not symbols:
            return Response(
                {'error': 'At least one symbol is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get historical data for all symbols
        data = {}
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1y")
            data[symbol] = hist['Close']
        
        # Calculate correlation matrix
        df = pd.DataFrame(data)
        correlation_matrix = df.corr()
        
        return Response(correlation_matrix.to_dict())
    
    @action(detail=False, methods=['get'])
    def risk_metrics(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        
        # Calculate risk metrics
        returns = hist['Close'].pct_change()
        risk_metrics = {
            'volatility': returns.std() * np.sqrt(252) * 100,  # Annualized volatility
            'sharpe_ratio': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': ((hist['Close'] / hist['Close'].cummax() - 1) * 100).min(),
            'var_95': returns.quantile(0.05) * 100,  # 95% Value at Risk
            'beta': stock.info.get('beta', 0)
        }
        
        return Response(risk_metrics)
    
    @action(detail=False, methods=['get'])
    def earnings_analysis(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock data
        stock = yf.Ticker(symbol)
        
        # Get earnings data
        earnings = stock.earnings
        if earnings.empty:
            return Response(
                {'error': 'No earnings data available.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate earnings metrics
        earnings_metrics = {
            'revenue_growth': ((earnings['Revenue'].iloc[-1] - earnings['Revenue'].iloc[-2]) / earnings['Revenue'].iloc[-2] * 100) if len(earnings) > 1 else 0,
            'earnings_growth': ((earnings['Earnings'].iloc[-1] - earnings['Earnings'].iloc[-2]) / earnings['Earnings'].iloc[-2] * 100) if len(earnings) > 1 else 0,
            'profit_margin': (earnings['Earnings'].iloc[-1] / earnings['Revenue'].iloc[-1] * 100) if earnings['Revenue'].iloc[-1] > 0 else 0,
            'historical_data': {
                'dates': earnings.index.strftime('%Y-%m-%d').tolist(),
                'revenue': earnings['Revenue'].tolist(),
                'earnings': earnings['Earnings'].tolist()
            }
        }
        
        return Response(earnings_metrics)
    
    @action(detail=False, methods=['get'])
    def dividend_analysis(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock data
        stock = yf.Ticker(symbol)
        
        # Get dividend data
        dividends = stock.dividends
        if dividends.empty:
            return Response(
                {'error': 'No dividend data available.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate dividend metrics
        current_price = stock.info.get('regularMarketPrice', 0)
        dividend_metrics = {
            'current_yield': (dividends.iloc[-1] * 4 / current_price * 100) if current_price > 0 else 0,
            'dividend_growth': ((dividends.iloc[-1] - dividends.iloc[-2]) / dividends.iloc[-2] * 100) if len(dividends) > 1 else 0,
            'payout_ratio': stock.info.get('payoutRatio', 0) * 100,
            'historical_data': {
                'dates': dividends.index.strftime('%Y-%m-%d').tolist(),
                'amounts': dividends.tolist()
            }
        }
        
        return Response(dividend_metrics)
    
    @action(detail=False, methods=['get'])
    def sector_analysis(self, request):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stock data
        stock = yf.Ticker(symbol)
        
        # Get sector information
        sector = stock.info.get('sector', '')
        industry = stock.info.get('industry', '')
        
        if not sector:
            return Response(
                {'error': 'No sector information available.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get sector performance
        sector_etf = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financial Services': 'XLF',
            'Consumer Cyclical': 'XLY',
            'Communication Services': 'XLC',
            'Industrials': 'XLI',
            'Consumer Defensive': 'XLP',
            'Energy': 'XLE',
            'Basic Materials': 'XLB',
            'Real Estate': 'XLRE',
            'Utilities': 'XLU'
        }
        
        sector_performance = {}
        if sector in sector_etf:
            etf = yf.Ticker(sector_etf[sector])
            hist = etf.history(period="1y")
            sector_performance = {
                'performance': ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100),
                'volatility': hist['Close'].pct_change().std() * np.sqrt(252) * 100
            }
        
        return Response({
            'sector': sector,
            'industry': industry,
            'sector_performance': sector_performance,
            'company_info': {
                'market_cap': stock.info.get('marketCap', 0),
                'pe_ratio': stock.info.get('forwardPE', 0),
                'eps': stock.info.get('trailingEps', 0)
            }
        }) 