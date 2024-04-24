from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST,require_GET
import json
import jwt
from django.conf import settings
from .models import Transaction
from django.core import serializers

@csrf_exempt
@require_POST
def form_handler(request):
    try:
        if not request.body:
            raise SuspiciousOperation('Missing JSON data in the request body')
        print(request.body)
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

        return JsonResponse({'status': 'success', 'message': 'Data received and processed successfully'},status = 200)

    except Exception as e:
        print('Error processing data:', e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)

@csrf_exempt
@require_POST
def graph_data_sender(request):
    try:
        print(request.headers)
        details = json.loads(request.body)
        print(details.get('endDate'))
        authorization_header = request.headers.get('Authorization')

        decoded_token = jwt.decode(authorization_header, 'secret', algorithms=['HS256'])

        username = decoded_token['username']
        print(username)
        print(details)
        print("checkpoint 0")
        
        start_date = details.get('startDate')
        end_date = details.get('startDate')
        
        print("checkpoint 1")
        
        transactions = Transaction.objects.filter(
            end_date__range=[start_date, end_date],
            name=username 
        )
        #print(transactions)
        serialized_transactions = serializers.serialize('json', transactions)
        parsed_transactions = json.loads(serialized_transactions)
        
        data_structure= []
        for transaction in parsed_transactions:
            fields = transaction['fields']
            data_structure.append({
                'type': fields.get('type'),
                'category': fields.get('category'),
                'amount': fields.get('amount'),
                'date':fields.get('end_date')
            })
        print("response: ", data_structure)
        return JsonResponse({'status':'true','message':'Data Passed','data':data_structure},status = 200)
    except Exception as e:
        print('Error processing data:', e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)