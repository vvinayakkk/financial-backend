from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import jwt
from django.conf import settings
from .models import Transaction

@csrf_exempt
@require_POST
def form_handler(request):
    try:
        if not request.body:
            raise SuspiciousOperation('Missing JSON data in the request body')

        # Extract JSON data from request body
        data = json.loads(request.body)
        json_string = data.get('jsonString')
        details = json.loads(json_string)

        # Extract and decode JWT token
        print(request.headers)
        authorization_header = request.headers.get('Authorization')
        if not authorization_header or ' ' not in authorization_header:
            raise SuspiciousOperation('Invalid Authorization header format')

        token = authorization_header.split(' ')[1]
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['username']

        # Create and save transaction
        transaction = Transaction(
            type=details.get('type'),
            name=username,  # Save username as the name
            category=details.get('category'),
            description=details.get('description'),
            amount=details.get('amount'),
            recurring=details.get('recurring'),
            term=details.get('term'),
            end_date=details.get('endDate')
        )
        transaction.save()

        return JsonResponse({'status': 'success', 'message': 'Data received and processed successfully'})

    except Exception as e:
        print('Error processing data:', e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)
