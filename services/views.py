from django.shortcuts import render

from finances.models import Category
from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST,require_GET
import json
import jwt
from django.conf import settings
from .models import Transaction
from django.core import serializers
import smtplib
from datetime import datetime, timedelta
from django.db.models import Sum
from users.models import User

@csrf_exempt
@require_POST
def form_handler(request):
    try:
        if not request.body:
            raise SuspiciousOperation('Missing JSON data in the request body')
        #print(request.body)
        data = json.loads(request.body)
        json_string = data.get('jsonString')
        details = json.loads(json_string)
        
        print(request.headers)
        
        authorization_header = request.headers.get('Authorization')
        print(authorization_header)

        decoded_token = jwt.decode(authorization_header, 'secret', algorithms=['HS256'])
        print(decoded_token)

        username = decoded_token['username']  # Access 'username' from the decoded token
        transaction = Transaction(
            type=details.get('type'),
            name=username,
            category=details.get('category'),
            description=details.get('description'),
            amount=details.get('amount'),
            recurring=details.get('recurring'),
            term=details.get('term'),
            end_date=details.get('endDate')
        )
        transaction.save()
        
        category=details.get('category') 
        print(category)
        
        check_offset(username,category)

        return JsonResponse({'status': 'success', 'message': 'Data received and processed successfully'},status = 200)

    except Exception as e:
        print('Error processing data:', e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)
    
def check_offset(username, category_name):
    print("Checking offset...")
    print("Username:", username)
    print("Category name:", category_name)
    
    category = Category.objects.filter(username=username, name=category_name).first()
    print("Category:", category)
    
    if category is None:
        print("No category found for the user.")
        return
    
    budget = category.budget
    print("Budget:", budget)
    
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Calculate the sum of amounts for the specified category and within the past 30 days
    total_amount = Transaction.objects.filter(category=category_name, end_date__gte=thirty_days_ago).aggregate(Sum('amount'))['amount__sum']
    print("Total amount spent in the last 30 days:", total_amount)
    
    if budget is not None and total_amount is not None and budget < total_amount:
        temp = User.objects.filter(username=username)
        if temp.exists():
            user = temp.first()
            email = user.email
            offset = total_amount - budget
            send_email(username, email, category_name, offset)
    else:
        print("No overspending detected.")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import jwt

@csrf_exempt
@require_POST
def graph_data_sender(request):
    try:
        details = json.loads(request.body)
        authorization_header = request.headers.get('Authorization')
        
        if not authorization_header:
            return JsonResponse({'status': 'error', 'message': 'Authorization header missing'}, status=400)

        decoded_token = jwt.decode(authorization_header, 'secret', algorithms=['HS256'])
        username = decoded_token['username']
        
        start_date_str = details.get('startDate')
        end_date_str = details.get('endDate')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        selected_option = details.get('selectedOption')
        
        # Filter transactions based on username, date range, and optional transaction type
        if selected_option == 'both':
            transactions = Transaction.objects.filter(
                end_date__range=[start_date, end_date],
                name=username 
            )
        else:
            transactions = Transaction.objects.filter(
                end_date__range=[start_date, end_date],
                name=username ,
                type = selected_option
            )
            
        # Serialize transactions to JSON format
        serialized_transactions = serializers.serialize('json', transactions)
        parsed_transactions = json.loads(serialized_transactions)
        
        # Construct response data structure
        data_structure = []
        for transaction in parsed_transactions:
            fields = transaction['fields']
            data_structure.append({
                'type': fields.get('type'),
                'category': fields.get('category'),
                'description': fields.get('description'),
                'amount': fields.get('amount'),
                'date': fields.get('end_date')
            })
        
        return JsonResponse({'status': 'true', 'message': 'Data Passed', 'data': data_structure}, status=200)
    
    except Exception as e:
        print('Error processing data:', e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)

    
def send_email(username, email, category, offset):
    
    server = smtplib.SMTP("smtp.office365.com", 587)
    server.starttls()
    server.login('jiten.ganwani@hotmail.com', 'Hmd2198%6')
    
    subject = 'Alert for overspending'
    message = f"Dear {username}, \nyou have overspent on {category} by {offset} in the last 30 days. Please remember to save more. \n\n Regards,\nRupies Team"
    msg = f'Subject: {subject}\n\n{message}'

    server.sendmail('jiten.ganwani@hotmail.com', email, msg)
    print("Email sent successfully")

    