from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserActivity, DataRequest
from django.utils import timezone


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('employee_id', 'first_name', 'last_name', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'employee_id' in self.fields:
            self.fields['employee_id'].help_text = 'Enter the employee ID (e.g., 010101)'
            self.fields['employee_id'].required = True
        if 'password1' in self.fields:
            self.fields['password1'].help_text = 'Password must be at least 8 characters long'
        if 'password2' in self.fields:
            self.fields['password2'].help_text = 'Enter the same password as before, for verification'


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('employee_id', 'first_name', 'last_name', 'email', 'role', 'account_status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'employee_id' in self.fields:
            self.fields['employee_id'].help_text = 'Employee ID cannot be changed once created'


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('employee_id', 'full_name', 'email', 'role', 'account_status', 'last_login', 'is_active', 'password_status')
    list_filter = ('role', 'account_status', 'is_active', 'is_staff', 'date_joined', 'last_login')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    ordering = ('employee_id',)
    
    fieldsets = (
        (None, {'fields': ('employee_id', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name', 'email')}),
        ('Account Settings', {'fields': ('role', 'account_status', 'is_active', 'is_staff', 'is_superuser')}),
        ('Password Management', {'fields': ('password_changed', 'password_changed_date', 'password_change_required')}),
        ('Account Status', {'fields': ('is_archived', 'archived_date', 'archived_by')}),
        ('Activity Tracking', {'fields': ('last_activity', 'login_count')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('date_joined', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'password_changed_date', 'archived_date', 'last_activity', 'login_count')
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def password_status(self, obj):
        if obj.password_change_required:
            return format_html('<span style="color: red;">⚠️ Change Required</span>')
        elif obj.password_changed:
            return format_html('<span style="color: green;">✅ Changed</span>')
        else:
            return format_html('<span style="color: orange;">⚠️ Default</span>')
    password_status.short_description = 'Password Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            # Admins can see all users except superadmins
            return qs.exclude(role=User.Role.SUPERADMIN)
        return qs.none()
    
    def has_add_permission(self, request):
        # Both superadmin and admin can create users
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        # Superadmin can edit anyone
        if request.user.role == User.Role.SUPERADMIN:
            return True
        # Admin can edit anyone except superadmins
        if request.user.role == User.Role.ADMIN:
            return obj.role != User.Role.SUPERADMIN
        return False
    
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        # Superadmin can delete anyone except themselves
        if request.user.role == User.Role.SUPERADMIN:
            return obj != request.user
        # Admin can delete field workers and other admins (but not superadmins)
        if request.user.role == User.Role.ADMIN:
            return obj.role != User.Role.SUPERADMIN and obj != request.user
        return False
    
    def save_model(self, request, obj, form, change):
        if not change:  # New user
            obj.password_change_required = True
        super().save_model(request, obj, form, change)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'severity', 'ip_address', 'timestamp', 'description_preview')
    list_filter = ('activity_type', 'severity', 'timestamp', 'user__role')
    search_fields = ('user__employee_id', 'user__first_name', 'user__last_name', 'description', 'ip_address')
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'user_agent', 'severity', 'metadata', 'timestamp')
    ordering = ('-timestamp',)
    
    def description_preview(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role == User.Role.SUPERADMIN


@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'request_type', 'requested_by', 'priority', 'status', 'requested_at', 'approved_by')
    list_filter = ('request_type', 'status', 'priority', 'requested_at', 'approved_at')
    search_fields = ('title', 'description', 'requested_by__employee_id', 'requested_by__first_name', 'approved_by__employee_id')
    readonly_fields = ('requested_by', 'requested_at', 'updated_at')
    ordering = ('-requested_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_type', 'title', 'description', 'priority', 'status')
        }),
        ('Request Details', {
            'fields': ('request_data', 'related_species', 'related_site')
        }),
        ('Approval Process', {
            'fields': ('approved_by', 'approved_at', 'admin_notes')
        }),
        ('Field Worker Notes', {
            'fields': ('field_worker_notes',)
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs.filter(status__in=[DataRequest.RequestStatus.PENDING, DataRequest.RequestStatus.APPROVED, DataRequest.RequestStatus.REJECTED])
        else:
            return qs.filter(requested_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.ADMIN, User.Role.FIELD_WORKER]
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN, User.Role.FIELD_WORKER]
        if obj.requested_by == request.user:
            return True
        if obj.status == DataRequest.RequestStatus.PENDING:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role == User.Role.SUPERADMIN
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == DataRequest.RequestStatus.APPROVED:
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)


# Customize admin site
admin.site.site_header = "AVICAST System Administration"
admin.site.site_title = "AVICAST Admin"
admin.site.index_title = "Welcome to AVICAST System Administration"
