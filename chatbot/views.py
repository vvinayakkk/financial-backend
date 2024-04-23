from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import google.generativeai as genai

# Configure Google Generative AI with the API key
#genai.configure(api_key='AIzaSyBVMjAduE6-gYb95ydSFauZH-bwin00N-Q')
genai.configure(api_key=os.environ.get('GENAI_API_KEY'))

# Initialize the GenerativeModel with the desired model name
model = genai.GenerativeModel('gemini-pro')

import json

@csrf_exempt
def chatbot_view(request):
    # Check if the request method is POST
    if request.method == 'POST':
        # Decode the request body JSON data
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        print(body_data)  # Print the entire JSON data
        
        # Extract the message from the JSON data
        message = body_data.get('message', '')
        print(f"Message: {message}")
        
        # Generate a response using the GenerativeModel
        response = model.generate_content(message)

        # Return the response as JSON
        return JsonResponse({'response': response.text})

    else:
        # Return a 405 Method Not Allowed error for other request methods
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
