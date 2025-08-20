from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from functools import wraps
from .models import User

def role_required(allowed_roles):
    """
    Decorator to check if user has required role(s)
    Usage: @role_required(['ADMIN', 'FIELD_WORKER'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not hasattr(request.user, 'role'):
                return redirect('login')
            
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # Redirect to home page if user doesn't have required role
                return redirect('home')
        
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """
    Decorator to check if user is ADMIN or SUPERADMIN
    """
    return role_required([User.Role.ADMIN, User.Role.SUPERADMIN])(view_func)

def superadmin_required(view_func):
    """
    Decorator to check if user is SUPERADMIN only
    """
    return role_required([User.Role.SUPERADMIN])(view_func)

def field_worker_required(view_func):
    """
    Decorator to check if user is FIELD_WORKER
    """
    return role_required([User.Role.FIELD_WORKER])(view_func)
