# views.py

import json
import random
import base64
import os
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from services.models import Transaction
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
import matplotlib.pyplot as plt
#from openai import GPT
#import openai

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ObjectDoesNotExist

from django.http import JsonResponse

import json
import os
import requests
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

'''@csrf_exempt
def chatbot_endpoint(request):
    if request.method == 'POST' or request.method == 'GET':
        try:
            data = json.loads(request.body)
            user_input = data.get('userInput', '')

            if not user_input:
                return JsonResponse({'error': 'Invalid request body'}, status=400)

            response = run_chat(user_input)

            return JsonResponse({'response': response})

        except Exception as e:
            print('Error in chat endpoint:', e)  # Log the error
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

def run_chat(user_input):
    try:
        # Replace with your API key
        #api_key = os.environ.get('API_KEY')

        # Define your model name
      #  model_name = "gemini-pro"

        # Make request to Generative AI API without predefined conversation history
        response = requests.post(
            'https://api.openai.com/v1/completions',
            headers={
                'Content-Type': 'application/json',
           #     'Authorization': f'Bearer {api_key}'
            },
            json={
        #        'model': model_name,
                'prompt': user_input,
                'max_tokens': 150
            }
        )

        if response.status_code == 200:
            generated_text = response.json().get('choices', [{}])[0].get('text', '')
            return generated_text
        else:
            return 'Failed to generate response from Generative AI API'

    except Exception as e:
        print('Error in run_chat:', e)'''

'''@csrf_exempt
def chatbot_handler(request):
    if request.method == 'POST':
        try:
            # Log the entire request body for debugging
            print("Request Body:", request.body)

            data = json.loads(request.body)  # Get the data sent by the frontend
            user_message = data.get('message')  # Extract the user's message from the data

            # Print the message from the frontend for debugging
            print("User Message:", user_message)

            # Send the user's message back as the response
            return JsonResponse({'response': user_message})

        except Exception as e:
            # Log any errors that occur
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    else:
        # Return an error response if the request method is not allowed
        return JsonResponse({'error': 'Method not allowed'}, status=405)'''
    
@csrf_exempt
def da(request):
    if request.method == 'POST':
        try:
            form_data = json.loads(request.body)
            json_data = json.loads(form_data['jsonString'])
            transaction = Transaction(
                type=json_data.get('type'),
                name=json_data.get('name', ' '),
                category=json_data.get('category'),
                description=json_data.get('description'),
                amount=json_data.get('amount'),
                recurring=json_data.get('recurring'),
                term=json_data.get('term'),
                end_date=json_data.get('endDate')
            )
            transaction.save()

            # Generate pie chart based on transaction categories for weekly transactions
            weekly_transactions = Transaction.objects.filter(term='weekly')
            weekly_categories = weekly_transactions.values('category').annotate(total=models.Count('category'))
            weekly_labels = [item['category'] for item in weekly_categories]
            weekly_totals = [item['total'] for item in weekly_categories]

            plt.figure(figsize=(8, 6))
            plt.pie(weekly_totals, labels=weekly_labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.tab20.colors)
            plt.title('Weekly Transaction Categories', fontsize=16)
            plt.axis('equal')
            weekly_pie_chart_path = os.path.join(settings.BASE_DIR, 'weekly_pie_chart.png')
            plt.tight_layout()
            plt.savefig(weekly_pie_chart_path)
            plt.close()

            # Generate bar chart based on transaction amounts for weekly transactions
            plt.figure(figsize=(10, 6))
            plt.bar(weekly_labels, weekly_totals, color=plt.cm.tab20.colors)
            plt.xlabel('Weekly Transaction Categories', fontsize=14)
            plt.ylabel('Total Amount', fontsize=14)
            plt.title('Weekly Transaction Amounts', fontsize=16)
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.tight_layout()
            weekly_bar_chart_path = os.path.join(settings.BASE_DIR, 'weekly_bar_chart.png')
            plt.savefig(weekly_bar_chart_path)
            plt.close()

            # Generate bar chart based on transaction amounts for monthly transactions
            monthly_transactions = Transaction.objects.filter(term='monthly')
            monthly_categories = monthly_transactions.values('category').annotate(total_amount=models.Sum('amount'))
            monthly_labels = [item['category'] for item in monthly_categories]
            monthly_totals = [item['total_amount'] for item in monthly_categories]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(monthly_labels, monthly_totals, color=plt.cm.tab20.colors)
            plt.xlabel('Monthly Transaction Categories', fontsize=14)
            plt.ylabel('Total Amount', fontsize=14)
            plt.title('Monthly Transaction Amounts', fontsize=16)
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.tight_layout()

            # Add total amounts as labels on top of each bar
            for bar, total in zip(bars, monthly_totals):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100, f'{total}', ha='center', va='bottom')

            monthly_bar_chart_path = os.path.join(settings.BASE_DIR, 'monthly_bar_chart.png')
            plt.savefig(monthly_bar_chart_path)
            plt.close()

            # Generate bar chart based on transaction amounts for yearly transactions
            yearly_transactions = Transaction.objects.filter(term='yearly')
            yearly_categories = yearly_transactions.values('category').annotate(total_amount=models.Sum('amount'))
            yearly_labels = [item['category'] for item in yearly_categories]
            yearly_totals = [item['total_amount'] for item in yearly_categories]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(yearly_labels, yearly_totals, color=plt.cm.tab20.colors)
            plt.xlabel('Yearly Transaction Categories', fontsize=14)
            plt.ylabel('Total Amount', fontsize=14)
            plt.title('Yearly Transaction Amounts', fontsize=16)
            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.tight_layout()

            # Add total amounts as labels on top of each bar
            for bar, total in zip(bars, yearly_totals):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100, f'{total}', ha='center', va='bottom')

            yearly_bar_chart_path = os.path.join(settings.BASE_DIR, 'yearly_bar_chart.png')
            plt.savefig(yearly_bar_chart_path)
            plt.close()

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        return HttpResponseNotAllowed(['POST'])

def dashboard(request, term):
    try:
        # Generate random values for income and expense
        get_random_value = lambda: random.randint(1, 1000)

        income = get_random_value()
        expense = get_random_value()

        if term == 'daily':
            # Daily calculations
            income *= 1.5
            expense *= 1.2
        elif term == 'weekly':
            # Weekly calculations
            income *= 7
            expense *= 6
        elif term == 'monthly':
            # Monthly calculations
            income *= 30
            expense *= 28
        elif term == 'yearly':
            # Yearly calculations
            income *= 365
            expense *= 360
        else:
            # Handle unknown terms or provide default values
            pass

        # Calculate balance
        balance = income - expense

        # Read the image file and encode it in base64
        image_path = os.path.join(settings.BASE_DIR, 'rickroll.jpg')  # Replace with the actual path to your image
        with open(image_path, 'rb') as image_file:
            image_url_base64 = f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"

        # Send the response with income, expense, balance, and base64-encoded image URL
        return JsonResponse({'income': income, 'expense': expense, 'balance': balance, 'imageUrlBase64': image_url_base64})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)