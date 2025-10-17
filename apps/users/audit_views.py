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
    """Redirect to admin_system audit logs
    
    Legacy endpoint - redirects to admin_system for better UX
    """
    # Check user permissions
    if not hasattr(request.user, 'role'):
        messages.error(request, "Access denied. User role not defined.")
        return redirect('login')
    
    if request.user.role not in ['ADMIN', 'SUPERADMIN']:
        messages.error(request, "Access denied. Admin privileges required to view system logs.")
        return redirect('locations:dashboard')
    
    # Redirect to admin_system audit logs
    messages.info(request, "System logs have been moved to the Admin System for better management.")
    return redirect('admin_system:admin_activities')


@login_required
def activity_details(request, activity_id):
    """AJAX endpoint to get detailed activity information"""
    try:
        activity = UserActivity.objects.select_related('user').get(id=activity_id)
        
        # Check permissions - only admin users can view activity details
        if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = {
            'id': activity.id,
            'activity_type': activity.get_activity_type_display(),
            'user': f"{activity.user.employee_id} - {activity.user.get_full_name()}",
            'timestamp': activity.timestamp.strftime('%B %d, %Y at %I:%M %p'),
            'description': activity.description,
            'ip_address': activity.ip_address or 'Not available',
            'user_agent': activity.user_agent or 'Not available',
            'severity': activity.get_severity_display(),
            'metadata': activity.metadata if activity.metadata else None
        }
        
        return JsonResponse(data)
        
    except UserActivity.DoesNotExist:
        return JsonResponse({'error': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
