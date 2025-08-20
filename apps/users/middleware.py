from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class SuperadminRestrictionMiddleware:
    """
    Middleware to restrict Superadmin users to only access admin panel
    and redirect them away from main dashboard features.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'role'):
            if request.user.role == 'SUPERADMIN':
                # List of URLs that Superadmin should not access
                restricted_urls = [
                    '/fauna/',
                    '/sites/',
                    '/census/',
                    '/reports/',
                    '/analytics/',
                ]
                
                # Check if current path is restricted
                current_path = request.path
                if any(current_path.startswith(url) for url in restricted_urls):
                    return redirect('admin:index')
                
                # If trying to access home page, redirect to admin
                if current_path == '/' and request.method == 'GET':
                    return redirect('admin:index')

        response = self.get_response(request)
        return response 