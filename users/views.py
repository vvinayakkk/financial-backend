from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer
from .models import User
import jwt, datetime

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import pyotp
import qrcode
import io
import base64

from .models import UserProfile, UserSession
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserProfileSerializer, PasswordChangeSerializer, TwoFactorSetupSerializer,
    TwoFactorVerifySerializer, UserSessionSerializer, SocialAuthSerializer
)

User = get_user_model()

class SignupView(APIView):
    def post(self, request):
        print("Received data:", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print("Signup dataset:", serializer.data)
            return JsonResponse({'message': 'Account created successfully'}, status=201)
        return JsonResponse(serializer.errors, status=400)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            payload = {
                'id': user.id,
                'username': user.username, 
                
            }

            token = jwt.encode(payload, 'secret', algorithm='HS256')
            print(token)
            response = JsonResponse({'status': True, 'message': 'Login successful','token':token})
            #response.set_cookie(key='jwt', value=token, httponly=True)
            #print(response.cookies)
            return response

        return JsonResponse({'status': False, 'error': 'Invalid username or password'}, status=401)

class UniqueCheckView(APIView):
    def post(self, request):
        email = request.data.get('email')
        contact = request.data.get('contact')

        if User.objects.filter(email=email).exists() or User.objects.filter(contact=contact).exists():
            return JsonResponse({'status': False, 'message': 'Email or contact already exists'})

        return JsonResponse({'status': True, 'message': 'Email and contact are unique'})

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data['email'])
            refresh = RefreshToken.for_user(user)
            
            # Create or update user session
            UserSession.objects.create(
                user=user,
                session_key=refresh.access_token,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            return Response({
                'access': str(token.access_token),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Deactivate user session
            UserSession.objects.filter(
                user=request.user,
                session_key=request.auth
            ).update(is_active=False)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def social_auth(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        if serializer.is_valid():
            # Implement social authentication logic here
            # This would typically involve verifying the token with the provider
            # and either creating a new user or logging in an existing one
            pass
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Wrong password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def setup_2fa(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.phone_number = serializer.validated_data['phone_number']
            
            # Generate TOTP secret
            totp = pyotp.TOTP(pyotp.random_base32())
            user.totp_secret = totp.secret
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp.provisioning_uri(
                user.email,
                issuer_name="Financial Tracker"
            ))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert QR code to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code = base64.b64encode(buffer.getvalue()).decode()
            
            user.save()
            return Response({
                'qr_code': qr_code,
                'secret': totp.secret
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            totp = pyotp.TOTP(user.totp_secret)
            
            if totp.verify(serializer.validated_data['code']):
                user.two_factor_enabled = True
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'code': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        sessions = UserSession.objects.filter(user=request.user)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def terminate_session(self, request):
        session_key = request.data.get('session_key')
        try:
            session = UserSession.objects.get(
                user=request.user,
                session_key=session_key
            )
            session.is_active = False
            session.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Session not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get personalized investment and budget recommendations based on user's financial data."""
        user = request.user
        
        # Get user's financial data
        accounts = Account.objects.filter(user=user)
        transactions = Transaction.objects.filter(user=user)
        budgets = Budget.objects.filter(user=user)
        
        # Calculate financial metrics
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
        monthly_income = transactions.filter(
            type='income',
            date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_expenses = transactions.filter(
            type='expense',
            date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate savings rate
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0
        
        # Get category-wise spending
        category_spending = transactions.filter(
            type='expense',
            date__gte=timezone.now() - timedelta(days=30)
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Calculate emergency fund status
        emergency_fund_target = monthly_expenses * 6  # 6 months of expenses
        emergency_fund_ratio = (total_balance / emergency_fund_target * 100) if emergency_fund_target > 0 else 0
        
        # Generate investment recommendations
        investment_recommendations = []
        
        if emergency_fund_ratio < 100:
            investment_recommendations.append({
                'type': 'emergency_fund',
                'priority': 'high',
                'message': f'Build your emergency fund to cover 6 months of expenses (${emergency_fund_target:,.2f}). '
                          f'Current coverage: {emergency_fund_ratio:.1f}%'
            })
        
        if savings_rate < 20:
            investment_recommendations.append({
                'type': 'savings_rate',
                'priority': 'high',
                'message': f'Increase your savings rate. Current rate: {savings_rate:.1f}%. '
                          f'Target: 20% of income'
            })
        
        # Generate budget recommendations
        budget_recommendations = []
        
        # Analyze spending patterns
        for category in category_spending:
            category_name = category['category__name']
            amount = category['total']
            percentage = (amount / monthly_expenses * 100) if monthly_expenses > 0 else 0
            
            # Define category-specific thresholds
            thresholds = {
                'Housing': 30,
                'Transportation': 15,
                'Food': 15,
                'Entertainment': 10,
                'Shopping': 10,
                'Utilities': 10,
                'Healthcare': 10
            }
            
            if category_name in thresholds and percentage > thresholds[category_name]:
                budget_recommendations.append({
                    'category': category_name,
                    'priority': 'medium',
                    'message': f'Consider reducing {category_name} spending. '
                              f'Current: {percentage:.1f}% of monthly expenses, '
                              f'Recommended: {thresholds[category_name]}%'
                })
        
        # Add general budget recommendations
        if monthly_expenses > monthly_income:
            budget_recommendations.append({
                'type': 'overspending',
                'priority': 'high',
                'message': 'Your expenses exceed your income. Consider reducing discretionary spending.'
            })
        
        # Add investment allocation recommendations
        if emergency_fund_ratio >= 100 and savings_rate >= 20:
            investment_recommendations.append({
                'type': 'investment_allocation',
                'priority': 'medium',
                'message': 'Consider diversifying investments: '
                          '50% in low-risk (bonds, fixed deposits), '
                          '30% in medium-risk (index funds), '
                          '20% in high-risk (stocks)'
            })
        
        return Response({
            'financial_metrics': {
                'total_balance': total_balance,
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'savings_rate': savings_rate,
                'emergency_fund_ratio': emergency_fund_ratio
            },
            'investment_recommendations': investment_recommendations,
            'budget_recommendations': budget_recommendations
        })