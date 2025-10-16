"""
Custom Admin System URLs
"""

from django.urls import path
from . import views, backup_views

app_name = 'admin_system'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('roles/', views.roles_assignments, name='roles_assignments'),
    path('users/bulk-action/', views.bulk_user_action, name='bulk_user_action'),
    
    # System Monitoring
    path('monitoring/', views.system_monitoring, name='system_monitoring'),
    path('activities/', views.admin_activities, name='admin_activities'),
    
    # Data Export
    path('export/', views.export_data, name='export_data'),
    
    # Password Change
    path('password-change/', views.password_change, name='password_change'),
    
    # Backup Management
    path('backups/', backup_views.backup_management, name='backup_management'),
    path('backups/create/', backup_views.create_backup, name='create_backup'),
    path('backups/delete/', backup_views.delete_backup, name='delete_backup'),
    path('backups/download/<str:backup_name>/', backup_views.download_backup, name='download_backup'),
    path('backups/status/', backup_views.backup_status, name='backup_status'),
    path('backups/update-location/', backup_views.update_backup_location, name='update_backup_location'),
    path('backups/restore/', backup_views.restore_backup, name='restore_backup'),
]
