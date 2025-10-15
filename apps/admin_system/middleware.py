"""
Middleware to handle superadmin first login password change
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class SuperAdminPasswordChangeMiddleware(MiddlewareMixin):
    """
    Middleware to check if superadmin needs to change password on first login
    """
    
    def process_request(self, request):
        # Only check for authenticated superadmin users
        if (request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'SUPERADMIN'):
            
            # Check if this is the default superadmin (010101) and password hasn't been changed
            if (request.user.employee_id == '010101' and 
                not request.user.password_changed and
                request.path not in ['/admin-system/password-change/', '/logout/']):
                
                # Show password change message and redirect
                messages.warning(
                    request, 
                    'Please change your default password for security reasons.'
                )
                return redirect('admin_system:password_change')
        
        return None
