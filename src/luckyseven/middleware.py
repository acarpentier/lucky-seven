"""
Custom middleware for LuckySeven API
"""

from django.http import JsonResponse


class HealthCheckMiddleware:
    """
    Middleware to handle health check requests from AWS ELB.
    This bypasses all other middleware to avoid Site framework issues.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health/':
            return JsonResponse({'ok': True})
        
        return self.get_response(request)
