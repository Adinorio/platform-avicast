"""
Main views module for users app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .account_views import *
from .audit_views import *
from .dashboard_views import *
from .user_management_views import *

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Dashboard views
    'user_management_dashboard', 'user_management_list',

    # User management views
    'create_user', 'update_user',

    # Account views
    'change_password',

    # Audit views
    'system_logs',
]