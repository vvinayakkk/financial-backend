
from django.urls import path
from .views import form_handler
#from .views import chatbot_handler

urlpatterns = [
    path('form/', form_handler, name='form_handler'),


  
]
