from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    """
    Decorator to check if user has required role.
    Redirects to home if user doesn't have permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('login')

            if hasattr(request.user, 'role') and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')

        return wrapper
    return decorator

def admin_required(view_func):
    """Decorator to require admin role"""
    return role_required(['ADMIN', 'SUPERADMIN'])(view_func)

def superadmin_required(view_func):
    """Decorator to require superadmin role"""
    return role_required(['SUPERADMIN'])(view_func)

def field_worker_required(view_func):
    """Decorator to require field worker role"""
    return role_required(['FIELD_WORKER'])(view_func)