"""
Comprehensive Permission Enforcement System
Integrates RolePermission and UserPermission models with view decorators
"""

from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from apps.admin_system.models import RolePermission, UserPermission

User = get_user_model()


def get_user_effective_permissions(user):
    """
    Get effective permissions for a user, considering both role permissions and user overrides
    Returns a dictionary of permission_name: boolean
    """
    if not user.is_authenticated:
        return {}
    
    # Get role permission
    try:
        role_permission = RolePermission.objects.get(role=user.role)
    except RolePermission.DoesNotExist:
        # If no role permission exists, create it with defaults
        role_permission = RolePermission.objects.create(role=user.role)
    
    # Start with role permissions
    effective_permissions = {
        'can_generate_reports': role_permission.can_generate_reports,
        'can_modify_species': role_permission.can_modify_species,
        'can_add_sites': role_permission.can_add_sites,
        'can_add_birds': role_permission.can_add_birds,
        'can_process_images': role_permission.can_process_images,
        'can_access_weather': role_permission.can_access_weather,
        'can_access_analytics': role_permission.can_access_analytics,
        'can_manage_users': role_permission.can_manage_users,
    }
    
    # Apply user-specific overrides if they exist
    try:
        user_permission = UserPermission.objects.get(user=user)
        for key in effective_permissions:
            if hasattr(user_permission, key):
                user_override = getattr(user_permission, key)
                if user_override is not None:  # Only override if explicitly set
                    effective_permissions[key] = user_override
    except UserPermission.DoesNotExist:
        pass  # No user-specific overrides
    
    return effective_permissions


def has_permission(user, permission_name):
    """
    Check if user has a specific permission
    """
    if not user.is_authenticated:
        return False
    
    # SUPERADMIN always has all permissions
    if user.role == User.Role.SUPERADMIN:
        return True
    
    effective_permissions = get_user_effective_permissions(user)
    return effective_permissions.get(permission_name, False)


def permission_required(permission_name, redirect_url='home', message=None, show_403_page=True):
    """
    Decorator to require a specific permission
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            if not has_permission(request.user, permission_name):
                error_message = message or f"You do not have permission to access this feature."
                
                if show_403_page:
                    # Show detailed 403 error page like fauna views
                    messages.error(request, f"{error_message} Contact your administrator to request access.")
                    from django.shortcuts import render
                    
                    # Map permission names to feature names for better error messages
                    feature_map = {
                        'can_add_sites': 'Sites Management',
                        'can_add_birds': 'Census Management', 
                        'can_access_analytics': 'Analytics Dashboard',
                        'can_process_images': 'Image Processing',
                        'can_access_weather': 'Weather Dashboard',
                        'can_modify_species': 'Species Management',
                        'can_generate_reports': 'Report Generation',
                        'can_manage_users': 'User Management',
                    }
                    
                    feature_name = feature_map.get(permission_name, 'this feature')
                    
                    return render(request, '403.html', {
                        'message': f'Access denied. You do not have permission to access {feature_name.lower()}.',
                        'feature': feature_name
                    }, status=403)
                else:
                    # Use simple redirect with message (original behavior)
                    messages.error(request, error_message)
                    return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permissions_required(permissions_list, redirect_url='home', message=None):
    """
    Decorator to require multiple permissions (ALL must be true)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            for permission_name in permissions_list:
                if not has_permission(request.user, permission_name):
                    error_message = message or f"You do not have permission to access this feature."
                    messages.error(request, error_message)
                    return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def any_permission_required(permissions_list, redirect_url='home', message=None):
    """
    Decorator to require any of multiple permissions (ANY can be true)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            has_any_permission = any(has_permission(request.user, perm) for perm in permissions_list)
            
            if not has_any_permission:
                error_message = message or f"You do not have permission to access this feature."
                messages.error(request, error_message)
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common permissions
def can_generate_reports_required(view_func):
    return permission_required('can_generate_reports')(view_func)


def can_modify_species_required(view_func):
    return permission_required('can_modify_species')(view_func)


def can_add_sites_required(view_func):
    return permission_required('can_add_sites')(view_func)


def can_add_birds_required(view_func):
    return permission_required('can_add_birds')(view_func)


def can_process_images_required(view_func):
    return permission_required('can_process_images')(view_func)


def can_access_weather_required(view_func):
    return permission_required('can_access_weather')(view_func)


def can_access_analytics_required(view_func):
    return permission_required('can_access_analytics')(view_func)


def can_manage_users_required(view_func):
    return permission_required('can_manage_users')(view_func)


# Template context processor for permissions
def user_permissions(request):
    """
    Add user permissions to template context
    """
    if request.user.is_authenticated:
        return {
            'user_permissions': get_user_effective_permissions(request.user),
            'can_generate_reports': has_permission(request.user, 'can_generate_reports'),
            'can_modify_species': has_permission(request.user, 'can_modify_species'),
            'can_add_sites': has_permission(request.user, 'can_add_sites'),
            'can_add_birds': has_permission(request.user, 'can_add_birds'),
            'can_process_images': has_permission(request.user, 'can_process_images'),
            'can_access_weather': has_permission(request.user, 'can_access_weather'),
            'can_access_analytics': has_permission(request.user, 'can_access_analytics'),
            'can_manage_users': has_permission(request.user, 'can_manage_users'),
        }
    return {}
