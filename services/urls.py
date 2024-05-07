
from django.urls import path
from .views import form_handler,graph_data_sender
#from .views import chatbot_handler
# 
urlpatterns = [
    path('form/', form_handler, name='form_handler'),
    path('graph/',graph_data_sender)
]