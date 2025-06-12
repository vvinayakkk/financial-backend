import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import google.generativeai as genai
from langchain.llms import GoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import yfinance as yf
import pandas as pd
import numpy as np
from django.conf import settings
from django.db.models import Sum, Avg, Count
from finances.models import Transaction, Category, Account, Budget
from .models import StockNews, AIRecommendation, FinancialInsight, MarketAnalysis

# Initialize Gemini 2.0 Flash
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
llm = GoogleGenerativeAI(model_name="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY)

# Initialize Sentence Transformer for embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class AIService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Sentence Transformer."""
        return embedding_model.encode(texts).tolist()
    
    def generate_financial_recommendations(self, user) -> List[Dict[str, Any]]:
        """Generate personalized financial recommendations using Gemini 2.0 Flash."""
        # Gather user's financial data
        transactions = Transaction.objects.filter(user=user)
        accounts = Account.objects.filter(user=user)
        budgets = Budget.objects.filter(user=user)
        
        # Calculate financial metrics
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
        monthly_income = transactions.filter(
            type='income',
            date__gte=datetime.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_expenses = transactions.filter(
            type='expense',
            date__gte=datetime.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Prepare context for Gemini
        context = {
            'total_balance': total_balance,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'savings_rate': ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0,
            'recent_transactions': list(transactions.order_by('-date')[:10].values()),
            'budget_status': list(budgets.values())
        }
        
        # Create prompt template with improved context handling
        prompt = PromptTemplate(
            input_variables=["context"],
            template="""
            Based on the following financial data, provide personalized recommendations:
            
            Financial Data:
            {context}
            
            Please provide:
            1. Investment recommendations
            2. Budget optimization suggestions
            3. Savings opportunities
            4. Risk alerts
            5. General financial advice
            
            Format the response as a JSON with the following structure:
            {
                "recommendations": [
                    {
                        "type": "investment|budget|savings|risk|general",
                        "title": "Recommendation title",
                        "description": "Detailed description",
                        "confidence_score": 0.0-1.0,
                        "priority": "high|medium|low",
                        "action_items": ["action1", "action2"],
                        "expected_impact": "string"
                    }
                ]
            }
            """
        )
        
        # Generate recommendations with improved error handling
        try:
            chain = LLMChain(llm=llm, prompt=prompt)
            response = chain.run(context=context)
            
            # Parse and store recommendations
            recommendations = []
            parsed_response = eval(response)
            for rec in parsed_response['recommendations']:
                # Generate embeddings for the recommendation
                embedding = self.get_embeddings([rec['description']])[0]
                
                recommendation = AIRecommendation.objects.create(
                    user=user,
                    type=rec['type'],
                    title=rec['title'],
                    description=rec['description'],
                    confidence_score=rec['confidence_score'],
                    context_data=context,
                    embedding=embedding
                )
                recommendations.append(recommendation)
            
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def analyze_stock_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze stock news using Gemini 2.0 Flash for sentiment and impact analysis."""
        # Fetch recent news
        stock = yf.Ticker(symbol)
        news = stock.news
        
        analyzed_news = []
        for item in news:
            # Prepare context for Gemini
            context = {
                'title': item['title'],
                'content': item.get('content', ''),
                'source': item.get('source', ''),
                'published_at': item.get('publishedAt', ''),
                'symbol': symbol
            }
            
            # Create prompt for sentiment analysis with improved context
            prompt = PromptTemplate(
                input_variables=["context"],
                template="""
                Analyze the following stock news and provide sentiment and impact analysis:
                
                News:
                {context}
                
                Please provide:
                1. Sentiment score (-1.0 to 1.0)
                2. Impact score (0.0 to 1.0)
                3. Brief analysis
                4. Key points
                5. Market implications
                
                Format the response as a JSON:
                {
                    "sentiment_score": float,
                    "impact_score": float,
                    "analysis": "string",
                    "key_points": ["point1", "point2"],
                    "market_implications": "string"
                }
                """
            )
            
            try:
                # Generate analysis
                chain = LLMChain(llm=llm, prompt=prompt)
                response = chain.run(context=context)
                
                analysis = eval(response)
                # Generate embeddings for the news content
                embedding = self.get_embeddings([item['title'] + " " + item.get('content', '')])[0]
                
                news_item = StockNews.objects.create(
                    symbol=symbol,
                    title=item['title'],
                    content=item.get('content', ''),
                    source=item.get('source', ''),
                    published_at=datetime.fromtimestamp(item.get('publishedAt', 0)),
                    sentiment_score=analysis['sentiment_score'],
                    impact_score=analysis['impact_score'],
                    embedding=embedding,
                    key_points=analysis.get('key_points', []),
                    market_implications=analysis.get('market_implications', '')
                )
                analyzed_news.append(news_item)
            except Exception as e:
                print(f"Error analyzing news: {e}")
        
        return analyzed_news
    
    def generate_market_analysis(self, symbol: str) -> Dict[str, Any]:
        """Generate comprehensive market analysis using Gemini."""
        # Fetch stock data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        
        # Calculate technical indicators
        technical_indicators = {
            'sma_20': hist['Close'].rolling(window=20).mean().iloc[-1],
            'sma_50': hist['Close'].rolling(window=50).mean().iloc[-1],
            'rsi': self._calculate_rsi(hist['Close']),
            'macd': self._calculate_macd(hist['Close']),
            'bollinger_bands': self._calculate_bollinger_bands(hist['Close'])
        }
        
        # Fetch fundamental data
        fundamental_metrics = {
            'pe_ratio': stock.info.get('forwardPE', None),
            'market_cap': stock.info.get('marketCap', None),
            'dividend_yield': stock.info.get('dividendYield', None),
            'beta': stock.info.get('beta', None)
        }
        
        # Prepare context for Gemini
        context = {
            'symbol': symbol,
            'technical_indicators': technical_indicators,
            'fundamental_metrics': fundamental_metrics,
            'price_history': hist['Close'].tolist(),
            'volume_history': hist['Volume'].tolist()
        }
        
        # Create prompt for market analysis
        prompt = PromptTemplate(
            input_variables=["context"],
            template="""
            Analyze the following stock data and provide a comprehensive market analysis:
            
            Data:
            {context}
            
            Please provide:
            1. Technical analysis
            2. Fundamental analysis
            3. Market sentiment
            4. Price prediction
            5. Risk assessment
            
            Format the response as a JSON:
            {
                "technical_analysis": "string",
                "fundamental_analysis": "string",
                "market_sentiment": "string",
                "price_prediction": {
                    "short_term": float,
                    "medium_term": float,
                    "long_term": float
                },
                "risk_assessment": "string",
                "confidence_score": float
            }
            """
        )
        
        # Generate analysis
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run(context=context)
        
        try:
            analysis = eval(response)
            market_analysis = MarketAnalysis.objects.create(
                symbol=symbol,
                analysis_date=datetime.now().date(),
                technical_indicators=technical_indicators,
                fundamental_metrics=fundamental_metrics,
                ai_prediction=analysis,
                confidence_score=analysis['confidence_score']
            )
            return market_analysis
        except Exception as e:
            print(f"Error generating market analysis: {e}")
            return None
    
    def process_bill_upload(self, bill_upload) -> Dict[str, Any]:
        """Process uploaded bill using Gemini for data extraction."""
        # Read bill content
        content = self._extract_text_from_bill(bill_upload.file)
        
        # Prepare context for Gemini
        context = {
            'content': content,
            'file_name': bill_upload.file.name
        }
        
        # Create prompt for bill processing
        prompt = PromptTemplate(
            input_variables=["context"],
            template="""
            Extract the following information from the bill:
            
            Bill Content:
            {context}
            
            Please extract:
            1. Total amount
            2. Date
            3. Vendor/Merchant
            4. Items/Services
            5. Tax amount
            6. Any other relevant information
            
            Format the response as a JSON:
            {
                "total_amount": float,
                "date": "YYYY-MM-DD",
                "vendor": "string",
                "items": ["string"],
                "tax_amount": float,
                "additional_info": {}
            }
            """
        )
        
        # Generate extraction
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run(context=context)
        
        try:
            extracted_data = eval(response)
            bill_upload.extracted_data = extracted_data
            bill_upload.processed = True
            bill_upload.save()
            return extracted_data
        except Exception as e:
            print(f"Error processing bill: {e}")
            return None
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return {
            'macd': macd.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': macd.iloc[-1] - signal_line.iloc[-1]
        }
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return {
            'upper': upper_band.iloc[-1],
            'middle': sma.iloc[-1],
            'lower': lower_band.iloc[-1]
        }
    
    def _extract_text_from_bill(self, file):
        """Extract text from uploaded bill file."""
        # Implement OCR or text extraction logic here
        # For now, return empty string
        return "" 