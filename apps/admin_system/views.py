"""
Custom Admin System Views
Beautiful, modern admin interface to replace Django admin
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
import json

from apps.fauna.models import Species
from apps.locations.models import Site, Census
from apps.image_processing.models import ImageUpload, ProcessingResult
from apps.users.models import UserActivity
from .models import AdminActivity, SystemConfiguration, AdminNotification

User = get_user_model()


def admin_required(user):
    """Check if user has admin privileges - ONLY SUPERADMIN can access admin system"""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'SUPERADMIN'


def superadmin_required(user):
    """Check if user has superadmin privileges"""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'SUPERADMIN'


def log_admin_activity(user, action_type, description, model_name=None, object_id=None, metadata=None):
    """Log admin activity for audit trail"""
    AdminActivity.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=None,  # Will be set in middleware
        user_agent=None,  # Will be set in middleware
        metadata=metadata or {}
    )


@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    """
    Beautiful admin dashboard with statistics and quick actions
    """
    # Get system statistics
    stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_species': Species.objects.filter(is_archived=False).count(),
        'total_sites': Site.objects.filter(is_archived=False).count(),
        'total_census': Census.objects.count(),
        'total_images': ImageUpload.objects.count(),
        'processed_images': ProcessingResult.objects.count(),
        'pending_images': ImageUpload.objects.filter(upload_status='CAPTURED').count(),
        'active_admins': User.objects.filter(role__in=['ADMIN', 'SUPERADMIN'], is_active=True).count(),
    }
    
    # Get recent activities
    recent_activities = AdminActivity.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Get system notifications (avoiding JSON field contains lookup for SQLite compatibility)
    notifications = AdminNotification.objects.filter(
        target_users=request.user
    ).filter(is_read=False, expires_at__isnull=True).order_by('-created_at')[:5]
    
    # Get recent user registrations
    recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:5]
    
    # Get system health metrics
    system_health = {
        'database_status': 'healthy',
        'disk_usage': '75%',  # This would be calculated from actual system metrics
        'memory_usage': '60%',
        'last_backup': timezone.now() - timezone.timedelta(days=1),
    }
    
    context = {
        'stats': stats,
        'recent_activities': recent_activities,
        'notifications': notifications,
        'recent_users': recent_users,
        'system_health': system_health,
        'page_title': 'System Administration Dashboard',
    }
    
    return render(request, 'admin_system/dashboard.html', context)


@login_required
@user_passes_test(admin_required)
def user_management(request):
    """
    Beautiful user management interface
    """
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'archived':
        users = users.filter(is_archived=True)
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    user_stats = {
        'total': User.objects.count(),
        'active': User.objects.filter(is_active=True).count(),
        'inactive': User.objects.filter(is_active=False).count(),
        'archived': User.objects.filter(is_archived=True).count(),
        'admins': User.objects.filter(role__in=['ADMIN', 'SUPERADMIN']).count(),
        'field_workers': User.objects.filter(role='FIELD_WORKER').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'user_stats': user_stats,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'page_title': 'User Management',
    }
    
    return render(request, 'admin_system/user_management.html', context)


@login_required
@user_passes_test(admin_required)
def user_detail(request, user_id):
    """
    Detailed user view with activity history
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get user activities
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
    
    # Get admin activities for this user
    admin_activities = AdminActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    
    context = {
        'user_obj': user,
        'activities': activities,
        'admin_activities': admin_activities,
        'page_title': f'User Details - {user.get_full_name()}',
    }
    
    return render(request, 'admin_system/user_detail.html', context)


@login_required
@user_passes_test(admin_required)
def user_edit(request, user_id):
    """
    Edit user information
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        user.save()
        
        log_admin_activity(
            request.user, 
            'UPDATE', 
            f'Updated user {user.get_full_name()}',
            'User',
            str(user.id),
            {'fields_updated': list(request.POST.keys())}
        )
        
        messages.success(request, f'User {user.get_full_name()} updated successfully.')
        return redirect('admin_system:user_detail', user_id=user.id)
    
    context = {
        'user_obj': user,
        'page_title': f'Edit User - {user.get_full_name()}',
    }
    
    return render(request, 'admin_system/user_edit.html', context)


@login_required
@user_passes_test(superadmin_required)
def system_monitoring(request):
    """
    System monitoring and health dashboard
    """
    # Database statistics
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        db_stats = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            db_stats[table_name] = count
    
    # Get recent system activities
    recent_activities = AdminActivity.objects.select_related('user').order_by('-timestamp')[:20]
    
    # Get error logs (if any)
    error_activities = AdminActivity.objects.filter(
        action_type='ERROR'
    ).order_by('-timestamp')[:10]
    
    # System configuration
    configurations = SystemConfiguration.objects.all().order_by('key')
    
    context = {
        'db_stats': db_stats,
        'recent_activities': recent_activities,
        'error_activities': error_activities,
        'configurations': configurations,
        'page_title': 'System Monitoring',
    }
    
    return render(request, 'admin_system/system_monitoring.html', context)


@login_required
@user_passes_test(admin_required)
def admin_activities(request):
    """
    View all admin activities for audit trail
    """
    activities = AdminActivity.objects.select_related('user').order_by('-timestamp')
    
    # Filter by action type
    action_filter = request.GET.get('action', '')
    if action_filter:
        activities = activities.filter(action_type=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        activities = activities.filter(user__employee_id__icontains=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'page_title': 'Admin Activities',
    }
    
    return render(request, 'admin_system/admin_activities.html', context)


@login_required
@user_passes_test(admin_required)
def bulk_user_action(request):
    """
    Handle bulk user actions (activate, deactivate, delete, etc.)
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            messages.error(request, 'No users selected.')
            return redirect('admin_system:user_management')
        
        users = User.objects.filter(id__in=user_ids)
        
        if action == 'activate':
            users.update(is_active=True)
            message = f'Activated {len(users)} users.'
        elif action == 'deactivate':
            users.update(is_active=False)
            message = f'Deactivated {len(users)} users.'
        elif action == 'archive':
            users.update(is_archived=True)
            message = f'Archived {len(users)} users.'
        elif action == 'unarchive':
            users.update(is_archived=False)
            message = f'Unarchived {len(users)} users.'
        else:
            messages.error(request, 'Invalid action.')
            return redirect('admin_system:user_management')
        
        log_admin_activity(
            request.user,
            'BULK_ACTION',
            f'Bulk action: {action} on {len(users)} users',
            'User',
            None,
            {'action': action, 'user_ids': user_ids, 'count': len(users)}
        )
        
        messages.success(request, message)
    
    return redirect('admin_system:user_management')


@login_required
@user_passes_test(superadmin_required)
def password_change(request):
    """
    Handle superadmin password change for first login
    """
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate old password
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'admin_system/password_change.html')
        
        # Validate new password
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'admin_system/password_change.html')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'admin_system/password_change.html')
        
        # Update password and mark as changed
        request.user.set_password(new_password)
        request.user.password_changed = True
        request.user.save()
        
        log_admin_activity(
            request.user,
            'UPDATE',
            'Changed default password',
            'User',
            str(request.user.id),
            {'password_changed': True}
        )
        
        messages.success(request, 'Password changed successfully!')
        return redirect('admin_system:admin_dashboard')
    
    return render(request, 'admin_system/password_change.html')


@login_required
@user_passes_test(admin_required)
def export_data(request):
    """
    Export data in various formats
    """
    export_type = request.GET.get('type', 'users')
    format_type = request.GET.get('format', 'csv')
    
    if export_type == 'users':
        users = User.objects.all()
        data = []
        for user in users:
            data.append({
                'Employee ID': user.employee_id,
                'Full Name': user.get_full_name(),
                'Email': user.email,
                'Role': user.role,
                'Status': 'Active' if user.is_active else 'Inactive',
                'Date Joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            })
    
    elif export_type == 'species':
        species = Species.objects.all()
        data = []
        for s in species:
            data.append({
                'Name': s.name,
                'Scientific Name': s.scientific_name,
                'Family': s.family,
                'IUCN Status': s.iucn_status,
                'Description': s.description,
                'Is Archived': s.is_archived,
            })
    
    else:
        messages.error(request, 'Invalid export type.')
        return redirect('admin_system:admin_dashboard')
    
    if format_type == 'json':
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    else:  # CSV
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    log_admin_activity(
        request.user,
        'EXPORT',
        f'Exported {export_type} data in {format_type} format',
        export_type.title(),
        None,
        {'export_type': export_type, 'format': format_type, 'record_count': len(data)}
    )
    
    return response
