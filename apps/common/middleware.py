"""
Enhanced Security Middleware for AVICAST
Implements comprehensive audit logging and security monitoring
"""

import logging
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import resolve
from django.conf import settings

from apps.users.models import UserActivity

User = get_user_model()
logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware:
    """
    Middleware to handle HTTPS requests in development
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # In development, we'll let HTTPS requests fail gracefully
        # The Django development server will handle the error message
        response = self.get_response(request)
        return response


class AuditLoggingMiddleware:
    """
    Comprehensive audit logging middleware for security monitoring
    Logs all user actions, admin operations, and security events
    """
    
    # Sensitive endpoints that require detailed logging
    SENSITIVE_ENDPOINTS = [
        '/admin-system/',
        '/users/',
        '/api/',
        '/image-processing/upload/',
        '/image-processing/process/',
        '/locations/import/',
        '/locations/export/',
    ]
    
    # Admin action patterns
    ADMIN_ACTIONS = [
        'create', 'edit', 'delete', 'bulk', 'import', 'export',
        'approve', 'reject', 'override', 'allocate'
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Log the request if it meets criteria
        self._log_request(request, response)
        
        return response

    def _log_request(self, request, response):
        """Log request details for audit purposes"""
        try:
            # Skip logging for static files and health checks
            if self._should_skip_logging(request):
                return
                
            # Determine if this is a sensitive request
            is_sensitive = self._is_sensitive_request(request)
            is_admin_action = self._is_admin_action(request)
            
            # Only log sensitive requests, admin actions, or errors
            if not (is_sensitive or is_admin_action or response.status_code >= 400):
                return
                
            # Get user information
            user = getattr(request, 'user', None)
            user_id = user.id if user and user.is_authenticated else None
            user_role = getattr(user, 'role', None) if user else None
            
            # Determine activity type
            activity_type = self._determine_activity_type(request, response)
            
            # Determine severity
            severity = self._determine_severity(request, response)
            
            # Create audit log entry (only if user is authenticated)
            if user_id:
                UserActivity.objects.create(
                    user_id=user_id,
                    activity_type=activity_type,
                    description=self._create_description(request, response),
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                    severity=severity,
                    metadata=self._extract_metadata(request, response),
                    timestamp=timezone.now()
                )
            
            # Also log to Django logger for immediate monitoring
            logger.info(
                f"AUDIT: {activity_type} | User: {user_id} | Role: {user_role} | "
                f"Path: {request.path} | Method: {request.method} | Status: {response.status_code} | "
                f"IP: {self._get_client_ip(request)}"
            )
            
        except Exception as e:
            # Don't let logging errors break the application
            logger.error(f"Audit logging error: {str(e)}")

    def _should_skip_logging(self, request):
        """Determine if request should be skipped for logging"""
        skip_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/ping/',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)

    def _is_sensitive_request(self, request):
        """Check if request is to a sensitive endpoint"""
        return any(request.path.startswith(endpoint) for endpoint in self.SENSITIVE_ENDPOINTS)

    def _is_admin_action(self, request):
        """Check if request contains admin action patterns"""
        path_lower = request.path.lower()
        return any(action in path_lower for action in self.ADMIN_ACTIONS)

    def _determine_activity_type(self, request, response):
        """Determine the type of activity based on request"""
        if response.status_code >= 500:
            return 'SYSTEM_ERROR'
        elif response.status_code >= 400:
            return 'CLIENT_ERROR'
        
        path = request.path
        method = request.method
        
        # More specific activity types based on path and method
        if path.startswith('/admin-system/'):
            if method == 'POST':
                if 'create' in path:
                    return 'USER_CREATED'
                elif 'edit' in path or 'update' in path:
                    return 'USER_UPDATED'
                elif 'delete' in path:
                    return 'USER_ARCHIVED'
                else:
                    return 'ADMIN_ACTION'
            else:
                return 'ADMIN_ACTION'
        
        elif path.startswith('/users/'):
            if method == 'POST':
                if 'create' in path:
                    return 'USER_CREATED'
                elif 'update' in path:
                    return 'USER_UPDATED'
                elif 'password-reset' in path:
                    return 'PASSWORD_CHANGE'
                else:
                    return 'USER_ACTION'
            else:
                return 'USER_ACTION'
        
        elif path.startswith('/fauna/'):
            if method == 'POST':
                if 'create' in path:
                    return 'SPECIES_ADDED'
                elif 'edit' in path or 'update' in path:
                    return 'SPECIES_UPDATED'
                elif 'delete' in path or 'archive' in path:
                    return 'SPECIES_ARCHIVED'
                else:
                    return 'SPECIES_ADDED'  # Default for fauna POST
            else:
                return 'SPECIES_ADDED'  # Default for fauna views
        
        elif path.startswith('/locations/'):
            if method == 'POST':
                if 'sites' in path and 'create' in path:
                    return 'SITE_ADDED'
                elif 'sites' in path and ('edit' in path or 'update' in path):
                    return 'SITE_UPDATED'
                elif 'census' in path and 'create' in path:
                    return 'CENSUS_ADDED'
                elif 'census' in path and ('edit' in path or 'update' in path):
                    return 'CENSUS_UPDATED'
                else:
                    return 'CENSUS_ADDED'  # Default for locations POST
            else:
                return 'CENSUS_ADDED'  # Default for locations views
        
        elif path.startswith('/image-processing/'):
            if method == 'POST':
                return 'IMAGE_PROCESSED'
            else:
                return 'IMAGE_PROCESSED'
        
        elif path.startswith('/analytics/'):
            if 'generate' in path or 'export' in path:
                return 'REPORT_GENERATED'
            elif 'import' in path:
                return 'DATA_IMPORTED'
            elif 'export' in path:
                return 'DATA_EXPORTED'
            else:
                return 'REPORT_GENERATED'
        
        elif path == '/login/':
            return 'LOGIN'
        elif path == '/logout/':
            return 'LOGOUT'
        
        elif path.startswith('/api/'):
            return 'API_ACCESS'
        
        else:
            return 'PAGE_VIEW'

    def _determine_severity(self, request, response):
        """Determine severity level based on request and response"""
        if response.status_code >= 500:
            return 'CRITICAL'
        elif response.status_code >= 400:
            return 'HIGH'
        elif request.path.startswith('/admin-system/'):
            return 'MEDIUM'
        elif self._is_sensitive_request(request):
            return 'MEDIUM'
        else:
            return 'LOW'

    def _create_description(self, request, response):
        """Create a human-readable description of the request"""
        method = request.method
        path = request.path
        status = response.status_code
        
        if status >= 400:
            return f"Error {status} on {method} {path}"
        
        # Create more meaningful descriptions based on the path
        description = self._get_meaningful_description(request, response)
        if description:
            return description
        else:
            return f"{method} {path}"
    
    def _get_meaningful_description(self, request, response):
        """Generate meaningful descriptions for common paths"""
        path = request.path
        method = request.method
        
        # Admin System paths
        if path.startswith('/admin-system/'):
            if path == '/admin-system/':
                return "Accessed Admin Dashboard"
            elif path == '/admin-system/users/':
                return "Viewed User Management"
            elif path.startswith('/admin-system/users/create'):
                return "Accessed User Creation Form"
            elif path.startswith('/admin-system/users/') and path.endswith('/edit/'):
                return "Accessed User Edit Form"
            elif path == '/admin-system/roles/':
                return "Viewed Roles & Assignments"
            elif path == '/admin-system/monitoring/':
                return "Viewed System Monitoring"
            elif path == '/admin-system/activities/':
                return "Viewed Admin Activities"
            elif path == '/admin-system/backups/':
                return "Viewed Backup Management"
            else:
                return f"Accessed Admin System: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # User Management paths
        elif path.startswith('/users/'):
            if path == '/users/audit-logs/':
                return "Viewed System Logs"
            elif path == '/users/dashboard/':
                return "Accessed User Dashboard"
            elif path == '/users/list/':
                return "Viewed User List"
            elif path.startswith('/users/create'):
                return "Accessed User Creation"
            elif path.startswith('/users/update/'):
                return "Accessed User Update"
            elif path.startswith('/users/password-reset/'):
                return "Accessed Password Reset"
            else:
                return f"Accessed User Management: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Locations paths
        elif path.startswith('/locations/'):
            if path == '/locations/':
                return "Accessed Locations Dashboard"
            elif path == '/locations/sites/':
                return "Viewed Sites"
            elif path == '/locations/census/':
                return "Viewed Census Data"
            elif path.startswith('/locations/sites/create'):
                return "Accessed Site Creation"
            elif path.startswith('/locations/census/create'):
                return "Accessed Census Creation"
            else:
                return f"Accessed Locations: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Fauna paths
        elif path.startswith('/fauna/'):
            if path == '/fauna/':
                return "Accessed Species Management"
            elif path == '/fauna/species/':
                return "Viewed Species List"
            elif path.startswith('/fauna/species/create'):
                return "Accessed Species Creation"
            elif path.startswith('/fauna/species/') and path.endswith('/edit/'):
                return "Accessed Species Edit"
            else:
                return f"Accessed Species Management: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Image Processing paths
        elif path.startswith('/image-processing/'):
            if path == '/image-processing/':
                return "Accessed Image Processing"
            elif path == '/image-processing/upload/':
                return "Accessed Image Upload"
            elif path == '/image-processing/results/':
                return "Viewed Processing Results"
            else:
                return f"Accessed Image Processing: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Analytics paths
        elif path.startswith('/analytics/'):
            if path == '/analytics/':
                return "Accessed Analytics Dashboard"
            elif path == '/analytics/reports/':
                return "Viewed Reports"
            elif path.startswith('/analytics/reports/generate'):
                return "Generated Report"
            else:
                return f"Accessed Analytics: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Weather paths
        elif path.startswith('/weather/'):
            if path == '/weather/':
                return "Accessed Weather Data"
            elif path == '/weather/forecast/':
                return "Viewed Weather Forecast"
            else:
                return f"Accessed Weather: {path.split('/')[-2] if len(path.split('/')) > 2 else 'Unknown'}"
        
        # Login/Logout paths
        elif path == '/login/':
            return "User Login"
        elif path == '/logout/':
            return "User Logout"
        elif path == '/':
            return "Accessed Home Page"
        
        return None

    def _get_client_ip(self, request):
        """Get the client's real IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _extract_metadata(self, request, response):
        """Extract additional metadata for logging"""
        metadata = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'referer': request.META.get('HTTP_REFERER', ''),
            'content_type': response.get('Content-Type', ''),
        }
        
        # Add query parameters if present
        if request.GET:
            metadata['query_params'] = dict(request.GET)
        
        # Add POST data for non-sensitive requests (be careful with this)
        if request.method == 'POST' and not self._is_sensitive_request(request):
            try:
                # Only log non-sensitive POST data
                post_data = {}
                for key, value in request.POST.items():
                    if key not in ['password', 'csrfmiddlewaretoken']:
                        post_data[key] = str(value)[:100]  # Truncate long values
                metadata['post_data'] = post_data
            except Exception:
                pass  # Don't fail if we can't extract POST data
        
        return metadata


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Only add HSTS in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response