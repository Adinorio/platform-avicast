"""
GTD-based Image Processing Permissions
Following Getting Things Done methodology for access control
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_required(view_func):
    """
    Decorator for views that require admin role
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.role not in ['ADMIN', 'SUPERADMIN']:
            raise PermissionDenied("Admin access required")

        return view_func(request, *args, **kwargs)

    return wrapper


def can_access_image_processing(user):
    """
    Check if user can access image processing features
    """
    if not user.is_authenticated:
        return False

    return user.role in ['ADMIN', 'SUPERADMIN']


def can_upload_images(user):
    """
    Check if user can upload images (Capture stage)
    """
    return can_access_image_processing(user)


def can_process_images(user):
    """
    Check if user can process images (Clarify stage)
    """
    return can_access_image_processing(user)


def can_review_results(user):
    """
    Check if user can review results (Reflect stage)
    """
    return can_access_image_processing(user)


def can_allocate_results(user):
    """
    Check if user can allocate results (Engage stage)
    """
    return can_access_image_processing(user)

