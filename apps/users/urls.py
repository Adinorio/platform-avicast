from django.urls import path

from . import views, audit_views, password_reset_views

app_name = "users"

urlpatterns = [
    # Password reset workflow
    path('password-reset/', password_reset_views.password_reset_request, name='password_reset_request'),
    path('password-reset/success/', password_reset_views.password_reset_success, name='password_reset_success'),
    path('password-reset/verify/<str:token>/', password_reset_views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/<str:token>/', password_reset_views.password_reset_confirm, name='password_reset_confirm'),
    
    # Admin password reset management
    path('password-reset/management/', password_reset_views.password_reset_management, name='password_reset_management'),
    path('password-reset/approve/<uuid:request_id>/', password_reset_views.password_reset_approve, name='password_reset_approve'),
    path('password-reset/bulk-action/', password_reset_views.password_reset_bulk_action, name='password_reset_bulk_action'),
    
    # System Monitoring (legacy - redirects to admin_system)
    path("audit-logs/", audit_views.system_logs, name="audit_logs"),
    path("audit-logs/<int:activity_id>/details/", audit_views.activity_details, name="activity_details"),
]
