"""
Password Reset Views for AVICAST
Secure password reset workflow for CENRO users
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .models import PasswordResetRequest, UserActivity
from .forms import (
    PasswordResetRequestForm, 
    PasswordResetVerificationForm, 
    PasswordResetApprovalForm,
    NewPasswordForm
)
from apps.admin_system.models import AdminNotification

User = get_user_model()


def password_reset_request(request):
    """Handle password reset requests from users"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            try:
                reset_request = form.save(request)
                
                # Log the request
                UserActivity.objects.create(
                    user=reset_request.user,
                    activity_type='PASSWORD_RESET_REQUEST',
                    description=f"Password reset requested by {reset_request.user.employee_id}",
                    ip_address=reset_request.requested_by_ip,
                    severity='MEDIUM'
                )
                
                # Create superadmin notification (only SUPERADMINs can manage password resets)
                superadmin_users = User.objects.filter(role=User.Role.SUPERADMIN, is_active=True)
                notification = AdminNotification.objects.create(
                    title="Password Reset Request",
                    message=f"User {reset_request.user.employee_id} ({reset_request.user.get_full_name()}) has requested a password reset. Reason: {reset_request.reason[:100]}...",
                    notification_type='SECURITY',
                    priority='MEDIUM',
                    target_roles=['SUPERADMIN']
                )
                notification.target_users.set(superadmin_users)
                
                messages.success(
                    request, 
                    f"Password reset request submitted successfully. "
                    f"Your request will be reviewed by a superadmin. "
                    f"Request ID: {reset_request.id}"
                )
                return redirect('users:password_reset_success')
                
            except Exception as e:
                messages.error(request, f"Error submitting request: {str(e)}")
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'users/password_reset_request.html', {
        'form': form,
        'title': 'Request Password Reset'
    })


def password_reset_success(request):
    """Show success message after password reset request"""
    return render(request, 'users/password_reset_success.html', {
        'title': 'Password Reset Request Submitted'
    })


def password_reset_verify(request, token):
    """Verify user identity before password reset"""
    try:
        reset_request = PasswordResetRequest.objects.get(
            reset_token=token,
            status=PasswordResetRequest.Status.APPROVED
        )
        
        # Check if token is expired
        if reset_request.is_expired():
            messages.error(request, "This password reset link has expired.")
            return redirect('users:password_reset_request')
        
    except PasswordResetRequest.DoesNotExist:
        messages.error(request, "Invalid or expired password reset link.")
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetVerificationForm(reset_request, request.POST)
        if form.is_valid():
            # Verification successful, redirect to password reset
            return redirect('users:password_reset_confirm', token=token)
    else:
        form = PasswordResetVerificationForm(reset_request)
    
    return render(request, 'users/password_reset_verify.html', {
        'form': form,
        'reset_request': reset_request,
        'title': 'Verify Your Identity'
    })


def password_reset_confirm(request, token):
    """Confirm new password after verification"""
    try:
        reset_request = PasswordResetRequest.objects.get(
            reset_token=token,
            status=PasswordResetRequest.Status.APPROVED
        )
        
        if reset_request.is_expired():
            messages.error(request, "This password reset link has expired.")
            return redirect('users:password_reset_request')
        
    except PasswordResetRequest.DoesNotExist:
        messages.error(request, "Invalid password reset link.")
        return redirect('users:password_reset_request')
    
    if request.method == 'POST':
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            # Set new password
            user = reset_request.user
            user.set_password(form.cleaned_data['new_password'])
            user.password_changed = True
            user.password_changed_date = timezone.now()
            user.password_change_required = False
            user.save()
            
            # Mark reset as completed
            reset_request.complete_reset()
            
            # Log the password change
            UserActivity.objects.create(
                user=user,
                activity_type='PASSWORD_CHANGED',
                description=f"Password changed via reset request {reset_request.id}",
                ip_address=request.META.get('REMOTE_ADDR', ''),
                request_path=request.path,
                request_method=request.method,
                severity='HIGH'
            )
            
            messages.success(request, "Password changed successfully. You can now log in with your new password.")
            return redirect('login')
    else:
        form = NewPasswordForm()
    
    return render(request, 'users/password_reset_confirm.html', {
        'form': form,
        'reset_request': reset_request,
        'title': 'Set New Password'
    })


@login_required
def password_reset_management(request):
    """Superadmin view for managing password reset requests"""
    # Check if user has superadmin privileges (only SUPERADMINs can manage password resets)
    if request.user.role != 'SUPERADMIN':
        messages.error(request, "Access denied. Superadmin privileges required for password reset management.")
        return redirect('home')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    user_filter = request.GET.get('user', '')
    date_filter = request.GET.get('date', '')
    
    # Base queryset
    requests = PasswordResetRequest.objects.select_related('user', 'approved_by').order_by('-requested_at')
    
    # Apply filters
    if status_filter:
        requests = requests.filter(status=status_filter)
    if user_filter:
        requests = requests.filter(user__employee_id__icontains=user_filter)
    if date_filter:
        requests = requests.filter(requested_at__date=date_filter)
    
    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': PasswordResetRequest.objects.count(),
        'pending': PasswordResetRequest.objects.filter(status='PENDING').count(),
        'approved': PasswordResetRequest.objects.filter(status='APPROVED').count(),
        'rejected': PasswordResetRequest.objects.filter(status='REJECTED').count(),
        'completed': PasswordResetRequest.objects.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'users/password_reset_management.html', {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'user_filter': user_filter,
        'date_filter': date_filter,
        'title': 'Password Reset Management'
    })


@login_required
def password_reset_approve(request, request_id):
    """Approve or reject a password reset request"""
    # Check if user has superadmin privileges (only SUPERADMINs can manage password resets)
    if request.user.role != 'SUPERADMIN':
        messages.error(request, "Access denied. Superadmin privileges required for password reset management.")
        return redirect('home')
    
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id)
    
    if not reset_request.can_be_approved():
        messages.error(request, "This request cannot be approved (expired or already processed).")
        return redirect('users:password_reset_management')
    
    if request.method == 'POST':
        form = PasswordResetApprovalForm(request.POST, instance=reset_request)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['approval_notes']
            
            if action == 'approve':
                if reset_request.approve(request.user, notes):
                    messages.success(request, f"Password reset request approved for {reset_request.user.employee_id}")
                    
                    # Log the approval
                    UserActivity.objects.create(
                        user=request.user,
                        activity_type='PASSWORD_RESET_APPROVED',
                        description=f"Approved password reset for {reset_request.user.employee_id}",
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        severity='HIGH'
                    )
                    
                    # Create user notification
                    user_notification = AdminNotification.objects.create(
                        title="Password Reset Approved",
                        message=f"Your password reset request has been approved by {request.user.get_full_name()}. You can now reset your password using the link provided.",
                        notification_type='SUCCESS',
                        priority='HIGH',
                        target_users=[reset_request.user]
                    )
                else:
                    messages.error(request, "Failed to approve request.")
            else:
                reset_request.reject(request.user, notes)
                messages.success(request, f"Password reset request rejected for {reset_request.user.employee_id}")
                
                # Log the rejection
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='PASSWORD_RESET_REJECTED',
                    description=f"Rejected password reset for {reset_request.user.employee_id}",
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    severity='HIGH'
                )
                
                # Create user notification
                user_notification = AdminNotification.objects.create(
                    title="Password Reset Rejected",
                    message=f"Your password reset request has been rejected by {request.user.get_full_name()}. Reason: {notes}",
                    notification_type='WARNING',
                    priority='MEDIUM',
                    target_users=[reset_request.user]
                )
            
            return redirect('users:password_reset_management')
    else:
        form = PasswordResetApprovalForm(instance=reset_request)
    
    return render(request, 'users/password_reset_approve.html', {
        'form': form,
        'reset_request': reset_request,
        'title': f'Review Password Reset Request - {reset_request.user.employee_id}'
    })


@login_required
@require_http_methods(["POST"])
def password_reset_bulk_action(request):
    """Handle bulk actions on password reset requests"""
    # Check if user has superadmin privileges (only SUPERADMINs can manage password resets)
    if request.user.role != 'SUPERADMIN':
        return JsonResponse({'error': 'Access denied. Superadmin privileges required.'}, status=403)
    
    action = request.POST.get('action')
    request_ids = request.POST.getlist('request_ids')
    
    if not action or not request_ids:
        return JsonResponse({'error': 'Invalid action or no requests selected'}, status=400)
    
    try:
        requests = PasswordResetRequest.objects.filter(id__in=request_ids)
        
        if action == 'approve':
            approved_count = 0
            for req in requests:
                if req.can_be_approved():
                    req.approve(request.user, "Bulk approval")
                    approved_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Approved {approved_count} password reset requests'
            })
        
        elif action == 'reject':
            for req in requests:
                if req.status == 'PENDING':
                    req.reject(request.user, "Bulk rejection")
            
            return JsonResponse({
                'success': True,
                'message': f'Rejected {len(requests)} password reset requests'
            })
        
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
