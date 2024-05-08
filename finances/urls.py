# finances/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('addcategory', views.add_category, name='add-category'),
    path('deletecategory', views.delete_category, name='delete-category'),
    path('reloadcategories', views.reload_categories, name='reload-categories'),
    path('updatebudget/', views.update_budget, name='update-budget'),
]