from django.urls import path

from . import views, audit_views, password_reset_views

app_name = "users"

urlpatterns = [
    # User Management Dashboard
    path("dashboard/", views.user_management_dashboard, name="user_management_dashboard"),
    path("list/", views.user_management_list, name="user_management_list"),
    path("create/", views.create_user, name="create_user"),
    path("update/<int:user_id>/", views.update_user, name="update_user"),
    path("logs/", views.system_logs, name="system_logs"),
    
    # Password reset workflow
    path('password-reset/', password_reset_views.password_reset_request, name='password_reset_request'),
    path('password-reset/success/', password_reset_views.password_reset_success, name='password_reset_success'),
    path('password-reset/verify/<str:token>/', password_reset_views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/<str:token>/', password_reset_views.password_reset_confirm, name='password_reset_confirm'),
    
    # Admin password reset management
    path('password-reset/management/', password_reset_views.password_reset_management, name='password_reset_management'),
    path('password-reset/approve/<uuid:request_id>/', password_reset_views.password_reset_approve, name='password_reset_approve'),
    path('password-reset/bulk-action/', password_reset_views.password_reset_bulk_action, name='password_reset_bulk_action'),
    
    # System Monitoring
    path("audit-logs/", audit_views.system_logs, name="audit_logs"),
    # Password Management
    path("change-password/", views.change_password, name="change_password"),
]
