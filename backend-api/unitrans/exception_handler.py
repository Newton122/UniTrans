"""
Custom DRF exception handler with detailed logging for debugging.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that logs details before returning response.
    """
    # Log the exception details
    request = context.get('request')
    view = context.get('view')
    
    print(f"\n===== EXCEPTION HANDLER =====")
    print(f"Exception type: {type(exc).__name__}")
    print(f"Exception: {exc}")
    print(f"View: {view}")
    print(f"Request method: {request.method if request else 'N/A'}")
    print(f"Request path: {request.path if request else 'N/A'}")
    print(f"Request body: {request.body if request else 'N/A'}")
    print(f"Request.data: {request.data if request else 'N/A'}")
    print(f"============================\n")
    
    logger.error(f"Exception {type(exc).__name__}: {exc}", extra={
        'view': str(view),
        'method': request.method if request else None,
        'path': request.path if request else None,
    })
    
    # Call the default exception handler to get the response
    response = exception_handler(exc, context)
    
    if response is not None:
        print(f"Exception response status: {response.status_code}")
        print(f"Exception response data: {response.data}")
    
    return response
