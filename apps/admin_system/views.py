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
from .models import AdminActivity, SystemConfiguration, AdminNotification, RolePermission
from .forms import UserCreateForm, UserEditForm, UserPasswordChangeForm

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
def user_create(request):
    """
    Create new user with auto-generated employee ID
    """
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                log_admin_activity(
                    request.user,
                    'CREATE',
                    f'Created user {user.get_full_name()} with ID {user.employee_id}',
                    'User',
                    str(user.id),
                    {
                        'employee_id': user.employee_id,
                        'role': user.role,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                )
                # Store credentials temporarily in session for display
                request.session['new_user_credentials'] = {
                    'employee_id': user.employee_id,
                    'password': form.cleaned_data.get('password'),
                    'user_name': user.get_full_name(),
                    'created_at': timezone.now().isoformat()
                }
                
                messages.success(request, f'User "{user.get_full_name()}" created successfully! Please note the credentials below.')
                return redirect('admin_system:user_credentials', user_id=user.id)
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    else:
        form = UserCreateForm()
    
    context = {
        'form': form,
        'title': 'Create New User',
        'subtitle': 'User will be assigned an auto-generated Employee ID'
    }
    
    return render(request, 'admin_system/user_form.html', context)


@login_required
@user_passes_test(admin_required)
def user_credentials(request, user_id):
    """
    Display newly created user credentials securely
    """
    user = get_object_or_404(User, id=user_id)
    credentials = request.session.get('new_user_credentials')
    
    # Clear credentials from session after displaying
    if credentials:
        del request.session['new_user_credentials']
    
    context = {
        'user_obj': user,
        'credentials': credentials,
        'page_title': f'User Credentials - {user.get_full_name()}',
    }
    
    return render(request, 'admin_system/user_credentials.html', context)


@login_required
@user_passes_test(admin_required)
def user_edit(request, user_id):
    """
    Edit user information
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            try:
                form.save()
                log_admin_activity(
                    request.user, 
                    'UPDATE', 
                    f'Updated user {user.get_full_name()}',
                    'User',
                    str(user.id),
                    {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'role': user.role
                    }
                )
                messages.success(request, f'User "{user.get_full_name()}" updated successfully.')
                return redirect('admin_system:user_detail', user_id=user.id)
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
    else:
        form = UserEditForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User - {user.get_full_name()}',
        'subtitle': f'Employee ID: {user.employee_id}'
    }
    
    return render(request, 'admin_system/user_form.html', context)


@login_required
@user_passes_test(lambda user: user.is_authenticated and hasattr(user, 'role') and user.role in ['ADMIN', 'SUPERADMIN'])
def system_monitoring(request):
    """
    System monitoring and health dashboard
    """
    # Database statistics with pagination
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        db_stats = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            db_stats[table_name] = count
    
    # Convert to list of tuples for pagination
    db_stats_list = [(table_name, count) for table_name, count in db_stats.items()]
    
    # Paginate database statistics
    paginator = Paginator(db_stats_list, 12)  # 12 items per page (4 rows of 3 columns)
    page_number = request.GET.get('page')
    db_stats_page = paginator.get_page(page_number)
    
    # Calculate start and end indices for display
    start_index = (db_stats_page.number - 1) * paginator.per_page + 1
    end_index = min(start_index + paginator.per_page - 1, paginator.count)
    
    # Get recent system activities
    recent_activities = AdminActivity.objects.select_related('user').order_by('-timestamp')[:20]
    
    # Get error logs (if any)
    error_activities = AdminActivity.objects.filter(
        action_type='ERROR'
    ).order_by('-timestamp')[:10]
    
    # System configuration
    configurations = SystemConfiguration.objects.all().order_by('key')
    
    context = {
        'db_stats': db_stats,  # Keep original for total count
        'db_stats_page': db_stats_page,  # Paginated data
        'start_index': start_index,  # Calculated start index
        'end_index': end_index,  # Calculated end index
        'recent_activities': recent_activities,
        'error_activities': error_activities,
        'configurations': configurations,
        'page_title': 'System Monitoring',
    }
    
    return render(request, 'admin_system/system_monitoring.html', context)


@login_required
@user_passes_test(superadmin_required)
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
    
    # Pagination with "Show All" option
    show_all = request.GET.get('show_all', '').strip()
    if show_all.lower() == 'true':
        page_obj = None
        activities_list = list(activities)
    else:
        paginator = Paginator(activities, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        activities_list = None
    
    context = {
        'page_obj': page_obj,
        'activities_list': activities_list,
        'show_all': show_all.lower() == 'true',
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
def roles_assignments(request):
    """
    Roles and Assignments management page
    """
    # Get or create role permissions
    role_permissions = {}
    for role_choice in User.Role.choices:
        role = role_choice[0]
        permission, created = RolePermission.objects.get_or_create(role=role)
        role_permissions[role] = permission
    
    # Get user counts by role
    user_counts = User.objects.values('role').annotate(count=Count('id'))
    role_counts = {item['role']: item['count'] for item in user_counts}
    
    # Ensure all roles are included in role_counts, even with 0 users
    for role_choice in User.Role.choices:
        role = role_choice[0]
        if role not in role_counts:
            role_counts[role] = 0
    
    if request.method == 'POST':
        role = request.POST.get('role')
        permission = role_permissions.get(role)
        
        if permission:
            # Store old permissions for comparison
            old_permissions = {
                'can_generate_reports': permission.can_generate_reports,
                'can_modify_species': permission.can_modify_species,
                'can_add_sites': permission.can_add_sites,
                'can_add_birds': permission.can_add_birds,
                'can_process_images': permission.can_process_images,
                'can_access_weather': permission.can_access_weather,
                'can_access_analytics': permission.can_access_analytics,
                'can_manage_users': permission.can_manage_users,
            }
            
            # Update permissions
            permission.can_generate_reports = 'can_generate_reports' in request.POST
            permission.can_modify_species = 'can_modify_species' in request.POST
            permission.can_add_sites = 'can_add_sites' in request.POST
            permission.can_add_birds = 'can_add_birds' in request.POST
            permission.can_process_images = 'can_process_images' in request.POST
            permission.can_access_weather = 'can_access_weather' in request.POST
            permission.can_access_analytics = 'can_access_analytics' in request.POST
            
            # SUPERADMIN always has User Management enabled
            if role == 'SUPERADMIN':
                permission.can_manage_users = True
            else:
                permission.can_manage_users = 'can_manage_users' in request.POST
            
            # Check for edge cases and provide warnings
            warnings = []
            if role == 'ADMIN':
                # Check if ADMIN has no permissions
                admin_permissions = [
                    permission.can_generate_reports,
                    permission.can_modify_species,
                    permission.can_add_sites,
                    permission.can_add_birds,
                    permission.can_process_images,
                    permission.can_access_weather,
                    permission.can_access_analytics,
                ]
                if not any(admin_permissions):
                    warnings.append("⚠️ ADMIN role has no main system permissions! This will severely limit their functionality.")
                
                # Check if ADMIN has User Management (not recommended)
                if permission.can_manage_users:
                    warnings.append("⚠️ ADMIN role has User Management access. This is unusual - consider if this is intended.")
            
            elif role == 'FIELD_WORKER':
                # Check if FIELD_WORKER has modification permissions
                modification_permissions = [
                    permission.can_generate_reports,
                    permission.can_modify_species,
                    permission.can_add_sites,
                    permission.can_add_birds,
                    permission.can_process_images,
                ]
                if any(modification_permissions):
                    warnings.append("⚠️ FIELD_WORKER role has modification permissions. This contradicts their typical view-only role.")
                
                # Check if FIELD_WORKER has User Management (not recommended)
                if permission.can_manage_users:
                    warnings.append("⚠️ FIELD_WORKER role has User Management access. This is unusual - consider if this is intended.")
            
            # Count active users with this role
            active_users = User.objects.filter(role=role, is_active=True).count()
            
            permission.save()
            
            # Create detailed success message
            success_msg = f"✅ {role} permissions updated successfully!"
            
            if active_users > 0:
                success_msg += f" This affects {active_users} active user(s)."
            
            if warnings:
                success_msg += "\n\n" + "\n".join(warnings)
                messages.warning(request, success_msg)
            else:
                messages.success(request, success_msg)
            
            # Log the permission changes
            changed_permissions = []
            for perm_name, old_value in old_permissions.items():
                new_value = getattr(permission, perm_name)
                if old_value != new_value:
                    changed_permissions.append(f"{perm_name}: {old_value} → {new_value}")
            
            if changed_permissions:
                log_admin_activity(
                    request.user,
                    'UPDATE',
                    f'Updated {role} permissions: {", ".join(changed_permissions)}',
                    'RolePermission',
                    str(permission.id),
                    {'role': role, 'changes': changed_permissions}
                )
            
            return redirect('admin_system:roles_assignments')
    
    # Create structured role data for template
    role_data = []
    for role_choice in User.Role.choices:
        role = role_choice[0]
        role_data.append({
            'role': role,
            'role_display': role_choice[1],
            'count': role_counts.get(role, 0),
            'permission': role_permissions.get(role)
        })
    
    context = {
        'role_permissions': role_permissions,
        'role_counts': role_counts,
        'user_roles': User.Role.choices,
        'role_data': role_data,
    }
    return render(request, 'admin_system/roles_assignments.html', context)


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
