"""
Debugging middleware to log all POST requests.
"""
import logging
import json

logger = logging.getLogger(__name__)

class LogRequestBodyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details for login endpoint
        if '/api/auth/login' in request.path:
            print(f"\n===== MIDDLEWARE: LoginRequest =====")
            print(f"Method: {request.method}")
            print(f"Content-Type: {request.content_type}")
            print(f"Content-Length: {request.META.get('CONTENT_LENGTH', 'N/A')}")
            print(f"Raw body: {request.body}")
            
            # Try to parse as JSON
            try:
                body_json = json.loads(request.body)
                print(f"Parsed JSON: {body_json}")
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
            
            print(f"====================================\n")
        
        response = self.get_response(request)
        return response
