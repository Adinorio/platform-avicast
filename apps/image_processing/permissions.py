"""
Shared permission decorators and utilities for image_processing app
"""

from functools import wraps
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect


def role_required(allowed_roles):
    """
    Decorator to check if user has required role

    Args:
        allowed_roles: List of allowed role strings (e.g., ["ADMIN", "FIELD_WORKER"])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Authentication required.")
                return redirect("login")

            if not hasattr(request.user, "role"):
                messages.error(request, "User role not defined.")
                return HttpResponse("User role not defined", status=403)

            if request.user.role not in allowed_roles:
                messages.error(request, "Access denied. Insufficient permissions.")
                return HttpResponse("Access denied. Insufficient permissions.", status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator for admin-only views"""
    return role_required(["ADMIN"])(view_func)


def staff_required(view_func):
    """Decorator for staff-only views (admin + field_worker)"""
    return role_required(["ADMIN", "FIELD_WORKER"])(view_func)


def superadmin_required(view_func):
    """Decorator for superadmin-only views"""
    return role_required(["SUPERADMIN"])(view_func)


def can_access_image(user, image):
    """
    Check if user can access a specific image

    Args:
        user: User instance
        image: ImageUpload instance

    Returns:
        bool: True if user can access the image
    """
    # Staff can access all images
    if user.is_staff:
        return True

    # Users can only access their own images
    return image.uploaded_by == user


def can_modify_image(user, image):
    """
    Check if user can modify a specific image

    Args:
        user: User instance
        image: ImageUpload instance

    Returns:
        bool: True if user can modify the image
    """
    # Staff can modify all images
    if user.is_staff:
        return True

    # Users can only modify their own images
    return image.uploaded_by == user and image.upload_status in [
        image.UploadStatus.UPLOADED,
        image.UploadStatus.FAILED
    ]


def can_review_results(user):
    """
    Check if user can review processing results

    Args:
        user: User instance

    Returns:
        bool: True if user can review results
    """
    return user.is_staff


def can_manage_models(user):
    """
    Check if user can manage AI models

    Args:
        user: User instance

    Returns:
        bool: True if user can manage models
    """
    return hasattr(user, "role") and user.role in ["ADMIN", "SUPERADMIN"]
