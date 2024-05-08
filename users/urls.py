from django.urls import path
from .views import SignupView, LoginView, UniqueCheckView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
    path('check/', UniqueCheckView.as_view(), name='unique-check'),
]