from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, UserActivity, DataRequest
from .forms import UserCreationForm, UserUpdateForm

@login_required
def user_management_dashboard(request):
    """Enhanced user management dashboard for superadmins"""
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Access denied. Superadmin only.')
        return redirect('home')

    # Dashboard statistics
    total_users = User.objects.count()
    active_admins = User.objects.filter(role='ADMIN', account_status='ACTIVE').count()
    active_field_workers = User.objects.filter(role='FIELD_WORKER', account_status='ACTIVE').count()

    # Recent activities (last 5)
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:5]

    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:5]

    # Pending requests
    pending_requests = DataRequest.objects.filter(status='PENDING').count()

    context = {
        'total_users': total_users,
        'active_admins': active_admins,
        'active_field_workers': active_field_workers,
        'recent_activities': recent_activities,
        'recent_users': recent_users,
        'pending_requests': pending_requests,
    }

    return render(request, 'users/user_management_dashboard.html', context)

@login_required
def user_management_list(request):
    """Enhanced user list with filtering and search"""
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Access denied. Superadmin only.')
        return redirect('home')

    # Get filter parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    archived_filter = request.GET.get('archived', 'false').lower() == 'true'

    # Build queryset
    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        users = users.filter(account_status=status_filter)

    if not archived_filter:
        users = users.filter(is_archived=False)

    # Pagination
    paginator = Paginator(users.order_by('-date_joined'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'archived_filter': archived_filter,
    }

    return render(request, 'users/user_management_list.html', context)

@login_required
def create_user(request):
    """Create new user account"""
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Access denied. Superadmin only.')
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.employee_id} created successfully!')
            return redirect('users:user_management_list')
    else:
        form = UserCreationForm()

    return render(request, 'users/create_user.html', {'form': form})

@login_required
def update_user(request, user_id):
    """Update existing user account"""
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Access denied. Superadmin only.')
        return redirect('home')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.employee_id} updated successfully!')
            return redirect('users:user_management_list')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'users/update_user.html', {'form': form, 'user': user})

@login_required
def change_password(request):
    """Handle password change for current user"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('users:change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('users:change_password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('users:change_password')

        request.user.set_password(new_password)
        request.user.mark_password_changed()
        request.user.save()

        messages.success(request, 'Password changed successfully!')
        return redirect('home')

    return render(request, 'users/change_password.html')

@login_required
def system_logs(request):
    """View system activity logs"""
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Access denied. Superadmin only.')
        return redirect('home')

    # Get filter parameters
    activity_filter = request.GET.get('activity_type', '')
    user_filter = request.GET.get('user', '')
    date_filter = request.GET.get('date', '')

    logs = UserActivity.objects.select_related('user').order_by('-timestamp')

    if activity_filter:
        logs = logs.filter(activity_type=activity_filter)

    if user_filter:
        logs = logs.filter(user_id=user_filter)

    if date_filter:
        logs = logs.filter(timestamp__date=date_filter)

    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'activity_filter': activity_filter,
        'user_filter': user_filter,
        'date_filter': date_filter,
    }

    return render(request, 'users/system_logs.html', context)
