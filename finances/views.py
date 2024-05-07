from django.shortcuts import render

# Create your views here.
# finances/views.py
import logging
from django.http import JsonResponse
from .models import Category
import json
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@csrf_exempt
def add_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Received data: {data}")
            # Process data and create a new category
            category = Category.objects.create(
                name=data['name'],
                type=data['type'],
                budget=data['budget']
            )
            logger.info(f"Created category: {category}")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception("Error adding category:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def delete_category(request):
    if request.method == 'POST':
        # Handle POST request to delete category
        data = json.loads(request.body)
        # Process data and delete the category
        # Example:
        try:
            category = Category.objects.get(name=data['name'], type=data['type'])
            category.delete()
            return JsonResponse({'status': 'success'})
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    elif request.method == 'GET':
        # Handle GET request for some other purpose, maybe fetching category details
        # Adjust the logic according to your requirements
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
@csrf_exempt
def reload_categories(request):
    if request.method == 'GET':
        try:
            # Retrieve all categories from the database
            categories = Category.objects.all()
            logger.info(f"Retrieved categories: {categories}")
            # Convert categories to JSON format
            categories_json = [{'name': category.name, 'type': category.type, 'budget': category.budget} for category in categories]
            # Return categories as JSON response
            return JsonResponse(categories_json, safe=False)
        except Exception as e:
            logger.exception("Error reloading categories:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def update_budget(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_name = data.get('category')
            category_type = data.get('type')
            new_budget = data.get('budget')

            category = Category.objects.get(name=category_name, type=category_type)
            category.budget = new_budget
            category.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception("Error updating budget:")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)