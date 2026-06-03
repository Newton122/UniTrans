from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

class DebugLoginTestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        import json
        print(f"\n===== DebugLoginTestView =====")
        print(f"Raw body: {request.body}")
        print(f"Decoded body: {request.body.decode('utf-8')}")
        print(f"Content-Type: {request.content_type}")
        print(f"request.data: {request.data}")
        print(f"request.data type: {type(request.data)}")
        
        return Response({
            'debug': {
                'body': request.body.decode('utf-8'),
                'content_type': request.content_type,
                'data': dict(request.data) if hasattr(request.data, 'items') else str(request.data),
            }
        })
