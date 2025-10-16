"""
Custom Admin System URLs
"""

from django.urls import path
from . import views

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
]
