from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('employee_id', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    ordering = ('employee_id',)
    
    fieldsets = (
        ('Authentication', {'fields': ('employee_id', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    def get_queryset(self, request):
        """Custom queryset to show users based on role"""
        qs = super().get_queryset(request)
        if request.user.role == 'SUPERADMIN':
            return qs  # Superadmin sees all users
        elif request.user.role == 'ADMIN':
            return qs.exclude(role='SUPERADMIN')  # Admin sees all except Superadmin
        else:
            return qs.filter(role='FIELD_WORKER')  # Field Worker sees only other Field Workers
    
    def has_add_permission(self, request):
        """Only Superadmin and Admin can add users"""
        return request.user.role in ['SUPERADMIN', 'ADMIN']
    
    def has_change_permission(self, request, obj=None):
        """Permission to change users"""
        if request.user.role == 'SUPERADMIN':
            return True
        elif request.user.role == 'ADMIN':
            return obj and obj.role != 'SUPERADMIN'
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only Superadmin can delete users"""
        return request.user.role == 'SUPERADMIN'
    
    def has_view_permission(self, request, obj=None):
        """Permission to view users"""
        if request.user.role == 'SUPERADMIN':
            return True
        elif request.user.role == 'ADMIN':
            return obj and obj.role != 'SUPERADMIN'
        return True  # Field Workers can view other Field Workers

# Customize admin site
admin.site.site_header = "AVICAST System - User Management"
admin.site.site_title = "AVICAST User Management"
admin.site.index_title = "Welcome to AVICAST User Management"
