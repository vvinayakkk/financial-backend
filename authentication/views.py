from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import openai
from openai import GPT


@csrf_exempt
def chatbot_view(request):
    if request.method == 'POST':
        # Assuming JSON request format directly from frontend
        try:
            json_data = json.loads(request.body.decode('utf-8'))
            query = json_data.get('question')

            # Debugging: Print the received query
            print("Received query:", query)
            
            # Initialize GPT-3.5 API
            gpt = GPT(api_key='')

            # Generate response using GPT-3.5 API
            response = gpt.submit_request(query)
            
            # Debugging: Print the generated query
            generated_query = response.choices[0].text.strip()
            print("Generated query:", generated_query)
            
            # Format response as JSON
            json_response = {'response': generated_query}
            
            return JsonResponse(json_response)

        except Exception as e:
            # Handle any exceptions
            return JsonResponse({'error': str(e)}, status=500)
            
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
