"""
Custom Admin System Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class RolePermission(models.Model):
    """Model to store dynamic role permissions"""
    role = models.CharField(max_length=50, choices=User.Role.choices, unique=True)
    
    # Feature permissions
    can_generate_reports = models.BooleanField(default=True)
    can_modify_species = models.BooleanField(default=True)
    can_add_sites = models.BooleanField(default=True)
    can_add_birds = models.BooleanField(default=True)
    can_process_images = models.BooleanField(default=True)
    can_access_weather = models.BooleanField(default=True)
    can_access_analytics = models.BooleanField(default=True)
    can_manage_users = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        """Override save to set default permissions based on role (only on creation)"""
        # Only set defaults on creation, allow manual changes after that
        if not self.pk:
            if self.role == 'SUPERADMIN':
                # SUPERADMIN: Only user management access by default
                self.can_generate_reports = False
                self.can_modify_species = False
                self.can_add_sites = False
                self.can_add_birds = False
                self.can_process_images = False
                self.can_access_weather = False
                self.can_access_analytics = False
                self.can_manage_users = True
            elif self.role == 'ADMIN':
                # ADMIN: All main system features by default
                self.can_generate_reports = True
                self.can_modify_species = True
                self.can_add_sites = True
                self.can_add_birds = True
                self.can_process_images = True
                self.can_access_weather = True
                self.can_access_analytics = True
                self.can_manage_users = False
            elif self.role == 'FIELD_WORKER':
                # FIELD_WORKER: View-only access by default
                self.can_generate_reports = False
                self.can_modify_species = False
                self.can_add_sites = False
                self.can_add_birds = False
                self.can_process_images = False
                self.can_access_weather = True
                self.can_access_analytics = True
                self.can_manage_users = False
        
        # Always enforce SUPERADMIN User Management
        if self.role == 'SUPERADMIN':
            self.can_manage_users = True
        
        super().save(*args, **kwargs)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
    
    def __str__(self):
        return f"{self.role} Permissions"


class AdminActivity(models.Model):
    """
    Track all admin activities for audit purposes
    """
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('BULK_ACTION', 'Bulk Action'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action_type} - {self.description[:50]}"


class SystemConfiguration(models.Model):
    """
    Store system-wide configuration settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, choices=[
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
        ('FLOAT', 'Float'),
    ], default='STRING')
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_configurations')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_configurations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['key']
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class AdminNotification(models.Model):
    """
    System notifications for administrators
    """
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
        ('SECURITY', 'Security Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    is_read = models.BooleanField(default=False)
    target_users = models.ManyToManyField(User, blank=True, related_name='admin_notifications')
    target_roles = models.JSONField(default=list, blank=True)  # List of roles that should see this
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class UserPermission(models.Model):
    """Model to override permissions for individual users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='permission_override')
    
    # Feature permissions - these override role permissions
    can_generate_reports = models.BooleanField(default=None, null=True, blank=True)
    can_modify_species = models.BooleanField(default=None, null=True, blank=True)
    can_add_sites = models.BooleanField(default=None, null=True, blank=True)
    can_add_birds = models.BooleanField(default=None, null=True, blank=True)
    can_process_images = models.BooleanField(default=None, null=True, blank=True)
    can_access_weather = models.BooleanField(default=None, null=True, blank=True)
    can_access_analytics = models.BooleanField(default=None, null=True, blank=True)
    can_manage_users = models.BooleanField(default=None, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_permission_overrides')
    
    class Meta:
        verbose_name = "User Permission Override"
        verbose_name_plural = "User Permission Overrides"
    
    def __str__(self):
        return f"{self.user.get_full_name()} Permission Override"
