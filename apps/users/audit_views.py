"""
Audit and logging views for users app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.db.models import Count, Q
from django.http import JsonResponse

from .models import UserActivity, User


@login_required
def system_logs(request):
    """View comprehensive system activity logs with monitoring dashboard
    
    Accessible by: ADMIN and SUPERADMIN only
    """
    # Check user permissions
    if not hasattr(request.user, 'role'):
        messages.error(request, "Access denied. User role not defined.")
        return redirect('login')
    
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, "Access denied. Admin privileges required to view system logs.")
        return redirect('locations:dashboard')
    
    # Set appropriate redirect URL based on user role
    if request.user.role == 'SUPERADMIN':
        request._redirect_url = 'admin_system:admin_dashboard'
    else:
        request._redirect_url = 'locations:dashboard'

    # Get filter parameters
    activity_filter = request.GET.get("activity_type", "")
    user_filter = request.GET.get("user", "")
    date_filter = request.GET.get("date", "")
    severity_filter = request.GET.get("severity", "")

    # Base queryset
    logs = UserActivity.objects.select_related("user").order_by("-timestamp")

    # Apply filters
    if activity_filter:
        logs = logs.filter(activity_type=activity_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if date_filter:
        logs = logs.filter(timestamp__date=date_filter)
    if severity_filter:
        logs = logs.filter(severity=severity_filter)

    # Get summary statistics
    total_activities = UserActivity.objects.count()
    species_activities = UserActivity.objects.filter(
        activity_type__in=['SPECIES_ADDED', 'SPECIES_UPDATED', 'SPECIES_ARCHIVED']
    ).count()
    census_activities = UserActivity.objects.filter(
        activity_type__in=['CENSUS_ADDED', 'CENSUS_UPDATED']
    ).count()
    image_activities = UserActivity.objects.filter(
        activity_type__in=['IMAGE_PROCESSED']
    ).count()

    # Get all users for filter dropdown
    users = User.objects.filter(is_active=True).order_by('employee_id')

    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_activities": total_activities,
        "species_activities": species_activities,
        "census_activities": census_activities,
        "image_activities": image_activities,
        "users": users,
        "current_activity": activity_filter,
        "current_user": user_filter,
        "current_date": date_filter,
        "current_severity": severity_filter,
    }

    return render(request, "users/audit_logs.html", context)
